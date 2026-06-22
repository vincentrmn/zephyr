"""Intégration : la pénalité de chauffage *calculée* par `thermal` alimente `roi`.

Boucle clé du §6 : plus de pénalité postulée à la main — elle vient du modèle
5R1C multi-zone (avec occupation), via l'orchestrateur `compute_roi_from_building`.
"""

from __future__ import annotations

from zephyr.climate import synthetic_climate
from zephyr.roi import ROIParameters, compute_roi
from zephyr.schemas import Building, Opening, Orientation, Room
from zephyr.study import compute_roi_from_building
from zephyr.thermal import R5C1Params


def _building() -> Building:
    rooms = [
        Room(
            id="sejour",
            area_m2=28.0,
            height_m=2.6,
            level=0,
            exterior_wall_orientations=[Orientation.S, Orientation.N],
            openings=[
                Opening(id="fs", area_m2=4.2, orientation=Orientation.S),
                Opening(id="fn", area_m2=1.8, orientation=Orientation.N),
            ],
        ),
        Room(
            id="chambre",
            area_m2=14.0,
            height_m=2.6,
            level=1,
            exterior_wall_orientations=[Orientation.E],
            openings=[Opening(id="fe", area_m2=1.8, orientation=Orientation.E)],
        ),
    ]
    return Building(id="b1", rooms=rooms)


def test_calculated_penalty_feeds_roi() -> None:
    occ = [3.0] * 7 + [8.0] * 3 + [4.0] * 7 + [8.0] * 4 + [3.0] * 3
    thermal, roi = compute_roi_from_building(
        _building(), synthetic_climate(), ROIParameters(), R5C1Params(gains_profile_24h_w_m2=occ)
    )

    # La pénalité vient bien du thermique, calculée et strictement positive.
    assert thermal.heating_penalty_eur_per_year > 0
    assert "calculée par thermal" in roi.assumptions["heating_penalty_source"]
    assert roi.sensitivity  # tornado présent

    # Et elle dégrade l'économie VNC vs une pénalité nulle.
    roi_zero = compute_roi(ROIParameters(), heating_penalty_eur_per_year=0.0)
    assert roi.npv_delta_eur < roi_zero.npv_delta_eur


def test_penalty_intensity_is_plausible() -> None:
    """La pénalité ramenée au m² reste dans un ordre de grandeur physique."""
    thermal, _ = compute_roi_from_building(_building(), synthetic_climate())
    area = _building().total_floor_area_m2
    per_m2_kwh = thermal.heating_penalty_kwh_per_year / area
    assert 0 < per_m2_kwh < 60  # kWh/m²/an, garde-fou de sanité
