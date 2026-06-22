"""Module `geometry` — reconstruction topologique → `Building` (Phase 3).

Reconstruit les pièces (polygones fermés), leurs labels, orientations et ouvrants
à partir des entités DXF brutes (`ingestion.RawDXF`). Le **code mesure** (surfaces
via shapely) ; le LLM n'intervient (plus tard) que pour le labelling sémantique.

⚠️ La reconstruction est **faillible** (CLAUDE.md §2.8) : orientations et ouvrants
sont des *estimations* destinées à être **validées/corrigées par l'ingénieur**
avant calcul. Les avertissements (`warnings`) signalent ce qui doit être vérifié.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from zephyr.ingestion import RawDXF
from zephyr.schemas import Building, InertiaClass, Opening, Orientation, Room, RoomLabel

# Mots-clés (texte/calque) → label de pièce.
_LABEL_KEYWORDS: list[tuple[tuple[str, ...], RoomLabel]] = [
    (("sejour", "séjour", "living", "salon"), RoomLabel.SEJOUR),
    (("chambre", "bedroom", "ch.", "chbre"), RoomLabel.CHAMBRE),
    (("cuisine", "kitchen"), RoomLabel.CUISINE),
    (("sdb", "bain", "bath", "douche", "sdd"), RoomLabel.SDB),
    (("wc", "toilet"), RoomLabel.WC),
    (
        ("couloir", "circulation", "hall", "palier", "degagement", "dégagement"),
        RoomLabel.CIRCULATION,
    ),
    (("bureau", "office"), RoomLabel.BUREAU),
    (("technique", "local", "garage", "buanderie", "cave", "grenier"), RoomLabel.TECHNIQUE),
]

_WINDOW_KEYWORDS = ("fenetre", "fenêtre", "window", "baie", "ouvr", "vitr")


@dataclass
class GeometryResult:
    """Bâtiment reconstruit + avertissements pour la validation humaine."""

    building: Building
    warnings: list[str] = field(default_factory=list)


def _label_from_text(text: str) -> RoomLabel | None:
    low = text.strip().lower()
    for keys, label in _LABEL_KEYWORDS:
        if any(k in low for k in keys):
            return label
    return None


def _orientations_from_vector(dx: float, dy: float) -> list[Orientation]:
    """Cardinal(s) d'exposition d'une pièce selon sa position vs centre bâtiment.

    Convention plan : +y = Nord, +x = Est. Pièce en périphérie → 1 façade ; près
    d'un coin (dx ~ dy) → 2 façades.
    """
    if dx == 0 and dy == 0:
        return []
    ns = Orientation.N if dy >= 0 else Orientation.S
    ew = Orientation.E if dx >= 0 else Orientation.W
    adx, ady = abs(dx), abs(dy)
    if adx > 2 * ady:
        return [ew]
    if ady > 2 * adx:
        return [ns]
    return [ns, ew]


def build_building(
    raw: RawDXF,
    *,
    hsp_m: float = 2.6,
    level: int = 0,
    inertia: InertiaClass = InertiaClass.LOURDE,
    min_area_m2: float = 2.0,
    max_area_m2: float = 2000.0,
    window_height_m: float = 1.3,
    building_id: str = "dxf",
) -> GeometryResult:
    """Reconstruit un `Building` depuis les entités DXF brutes.

    Pièces = polylignes fermées (surface shapely, filtrée par taille). Labels =
    texte contenu dans la pièce, sinon nom de calque. Orientations = estimées
    depuis la position vs centre du bâtiment. Ouvrants = segments sur un calque
    « fenêtre », rattachés à la pièce la plus proche.
    """
    from shapely.geometry import LineString, Point, Polygon

    warnings = list(raw.warnings)

    # 1) Polygones de pièces (fermés, taille plausible).
    room_polys: list[tuple[Polygon, str]] = []
    for pl in raw.polylines:
        if not pl.closed or len(pl.points) < 3:
            continue
        poly = Polygon(pl.points)
        if not poly.is_valid:
            poly = poly.buffer(0)
        if not isinstance(poly, Polygon) or poly.is_empty:
            continue
        if min_area_m2 <= poly.area <= max_area_m2:
            room_polys.append((poly, pl.layer))

    if not room_polys:
        warnings.append("Aucune pièce reconstructible (polylignes fermées de taille plausible).")
        return GeometryResult(Building(id=building_id, inertia_class=inertia), warnings)

    # Centre du bâtiment (moyenne des centroïdes).
    cx = sum(p.centroid.x for p, _ in room_polys) / len(room_polys)
    cy = sum(p.centroid.y for p, _ in room_polys) / len(room_polys)

    # 2) Fenêtres : segments sur un calque « fenêtre ».
    window_lines = [ln for ln in raw.lines if any(k in ln.layer.lower() for k in _WINDOW_KEYWORDS)]

    rooms: list[Room] = []
    labelled = 0
    for idx, (poly, layer) in enumerate(room_polys):
        c = poly.centroid

        # Label : texte contenu, sinon calque.
        label = RoomLabel.AUTRE
        for txt in raw.texts:
            if poly.contains(Point(txt.position)):
                found = _label_from_text(txt.text)
                if found:
                    label = found
                    break
        if label is RoomLabel.AUTRE:
            found = _label_from_text(layer)
            if found:
                label = found
        if label is not RoomLabel.AUTRE:
            labelled += 1

        orients = _orientations_from_vector(c.x - cx, c.y - cy)

        # Ouvrants : segments fenêtre dont le milieu est proche de la pièce.
        openings: list[Opening] = []
        for wl in window_lines:
            mid = Point((wl.start[0] + wl.end[0]) / 2, (wl.start[1] + wl.end[1]) / 2)
            if poly.distance(mid) <= 0.5:  # ~0,5 m de tolérance
                length = LineString([wl.start, wl.end]).length
                facing = orients[0] if orients else Orientation.S
                openings.append(
                    Opening(
                        id=f"r{idx}_win{len(openings)}",
                        area_m2=max(length * window_height_m, 0.1),
                        orientation=facing,
                        head_height_m=min(hsp_m - 0.2, window_height_m + 0.9),
                    )
                )

        rooms.append(
            Room(
                id=f"room_{idx}",
                label=label,
                area_m2=round(poly.area, 2),
                height_m=hsp_m,
                level=level,
                polygon=[(round(x, 3), round(y, 3)) for x, y in poly.exterior.coords],
                exterior_wall_orientations=orients,
                openings=openings,
            )
        )

    # 3) Avertissements de validation humaine.
    warnings.append("Orientations estimées depuis le plan — À VALIDER par l'ingénieur (§2.8).")
    if not window_lines:
        warnings.append("Aucun ouvrant détecté (pas de calque 'fenêtre') — à saisir manuellement.")
    if labelled < len(rooms):
        warnings.append(
            f"{len(rooms) - labelled}/{len(rooms)} pièce(s) non labellisées — à étiqueter."
        )

    building = Building(id=building_id, rooms=rooms, inertia_class=inertia)
    return GeometryResult(building, warnings)
