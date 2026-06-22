"""Module `viz` — rendu de la géométrie reconstruite (plan).

Donne à voir ce que `geometry` a reconstruit : pièces (polygones), labels,
ouvrants. Indispensable à la validation humaine (§2.8) — l'ingénieur doit
*voir* le plan extrait avant de faire confiance aux calculs.

Niveau pré-étude : un plan schématique par niveau, pas un rendu CAO.
"""

from __future__ import annotations

import base64
import io

from zephyr.schemas import Building, RoomLabel

# Couleurs par label (lisibilité, pas normatif).
_LABEL_COLOR: dict[RoomLabel, str] = {
    RoomLabel.SEJOUR: "#cfe8cf",
    RoomLabel.CHAMBRE: "#cfe0f5",
    RoomLabel.CUISINE: "#f5e6cf",
    RoomLabel.SDB: "#cfeef0",
    RoomLabel.WC: "#e6cff5",
    RoomLabel.CIRCULATION: "#eeeeee",
    RoomLabel.BUREAU: "#f5cfd6",
    RoomLabel.TECHNIQUE: "#dddddd",
    RoomLabel.AUTRE: "#f0f0f0",
}


def render_plan_png(building: Building) -> bytes:
    """Rend le plan reconstruit (un sous-graphe par niveau) en PNG.

    Chaque pièce est dessinée depuis son ``polygon``, colorée par label, annotée
    (id, label, surface) ; les pièces sans polygone sont ignorées (rien à tracer).
    """
    import matplotlib

    matplotlib.use("Agg")  # backend sans affichage
    import matplotlib.patches as mpatches
    import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon as MplPolygon

    rooms = [r for r in building.rooms if r.polygon and len(r.polygon) >= 3]
    levels = sorted({r.level for r in rooms}) or [0]

    fig, axes = plt.subplots(1, len(levels), figsize=(5 * len(levels), 5), squeeze=False)
    for ax, level in zip(axes[0], levels, strict=True):
        ax.set_title(f"Niveau {level}")
        ax.set_aspect("equal")
        ax.axis("off")
        for room in (r for r in rooms if r.level == level):
            color = _LABEL_COLOR.get(room.label, "#f0f0f0")
            ax.add_patch(MplPolygon(room.polygon, closed=True, facecolor=color, edgecolor="#333"))
            xs = [p[0] for p in room.polygon]
            ys = [p[1] for p in room.polygon]
            cx, cy = sum(xs) / len(xs), sum(ys) / len(ys)
            ax.text(
                cx,
                cy,
                f"{room.label.value}\n{room.area_m2:.0f} m²",
                ha="center",
                va="center",
                fontsize=8,
            )
            # Ouvrants : un petit trait bleu par ouvrant (schématique).
            for k, _op in enumerate(room.openings):
                x0 = min(xs) + 0.7 * k
                ax.plot([x0, x0 + 0.6], [min(ys), min(ys)], color="#1a73e8", lw=3)
        ax.relim()
        ax.autoscale_view()

    # Flèche Nord (+y).
    fig.text(0.01, 0.95, "N ↑", fontsize=11, weight="bold")
    legend = [
        mpatches.Patch(color=c, label=lbl.value)
        for lbl, c in _LABEL_COLOR.items()
        if any(r.label is lbl for r in rooms)
    ]
    if legend:
        fig.legend(handles=legend, loc="lower center", ncol=min(len(legend), 6), fontsize=8)

    buf = io.BytesIO()
    fig.tight_layout(rect=(0, 0.06, 1, 1))
    fig.savefig(buf, format="png", dpi=110)
    plt.close(fig)
    return buf.getvalue()


def render_plan_data_uri(building: Building) -> str:
    """Plan reconstruit en data-URI base64 (pour l'embarquer dans le rapport HTML)."""
    png = render_plan_png(building)
    return "data:image/png;base64," + base64.b64encode(png).decode("ascii")
