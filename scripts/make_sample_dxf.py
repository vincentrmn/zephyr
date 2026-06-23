"""Génère un plan DXF d'exemple (en mètres) pour tester la plateforme.

Sortie : ``examples/plan_exemple.dxf`` — pièces = polylignes fermées par calque,
labels = textes, ouvrants = segments sur le calque ``FENETRE``.

Lancer :  ``uv run --extra cao python scripts/make_sample_dxf.py``
"""

from __future__ import annotations

from pathlib import Path

import ezdxf

# (label, (x0, y0, x1, y1)) — rectangles de pièces en mètres.
_ROOMS = [
    ("Sejour", (0.0, 0.0, 6.0, 5.0)),
    ("Cuisine", (6.0, 0.0, 10.0, 5.0)),
    ("Chambre", (0.0, 5.0, 5.0, 9.0)),
    ("Chambre", (5.0, 5.0, 10.0, 9.0)),
    ("SDB", (0.0, 9.0, 3.0, 12.0)),
    ("Couloir", (3.0, 9.0, 10.0, 12.0)),
]

# Fenêtres : segments (x0, y0, x1, y1) posés sur les murs extérieurs.
_WINDOWS = [
    (1.0, 0.0, 3.0, 0.0),    # séjour sud
    (10.0, 1.0, 10.0, 3.5),  # cuisine est
    (0.0, 6.0, 0.0, 8.0),    # chambre 1 ouest
    (10.0, 6.0, 10.0, 8.0),  # chambre 2 est
    (1.0, 12.0, 2.0, 12.0),  # SDB nord
]


def main() -> None:
    doc = ezdxf.new(setup=True)
    doc.header["$INSUNITS"] = 6  # mètres
    msp = doc.modelspace()

    for label, (x0, y0, x1, y1) in _ROOMS:
        layer = label.upper()
        if layer not in doc.layers:
            doc.layers.add(layer)
        pts = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
        msp.add_lwpolyline(pts, close=True, dxfattribs={"layer": layer})
        msp.add_text(
            label,
            dxfattribs={"layer": "TEXTE", "height": 0.3},
        ).set_placement(((x0 + x1) / 2, (y0 + y1) / 2))

    if "FENETRE" not in doc.layers:
        doc.layers.add("FENETRE")
    for x0, y0, x1, y1 in _WINDOWS:
        msp.add_line((x0, y0), (x1, y1), dxfattribs={"layer": "FENETRE"})

    out = Path(__file__).resolve().parents[1] / "examples" / "plan_exemple.dxf"
    out.parent.mkdir(parents=True, exist_ok=True)
    doc.saveas(out)
    print("écrit", out)


if __name__ == "__main__":
    main()
