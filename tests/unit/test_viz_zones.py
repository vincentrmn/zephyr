"""Tests du rendu de plan (viz) et des sorties thermiques par pièce (saison + CO₂)."""

from __future__ import annotations

import pytest

from zephyr.climate import synthetic_climate
from zephyr.schemas import Building, Opening, Orientation, Room, RoomLabel
from zephyr.thermal import R5C1Params, simulate_5r1c

pytest.importorskip("matplotlib")
from zephyr.viz import render_plan_data_uri, render_plan_png  # noqa: E402


def _building() -> Building:
    rooms = [
        Room(
            id="sejour",
            label=RoomLabel.SEJOUR,
            area_m2=30.0,
            height_m=2.6,
            polygon=[(0, 0), (6, 0), (6, 5), (0, 5)],
            exterior_wall_orientations=[Orientation.S, Orientation.E],
            openings=[Opening(id="fs", area_m2=4.0, orientation=Orientation.S)],
        ),
        Room(
            id="chambre",
            label=RoomLabel.CHAMBRE,
            area_m2=16.0,
            height_m=2.6,
            polygon=[(0, 5), (4, 5), (4, 9), (0, 9)],
            exterior_wall_orientations=[Orientation.N],
            openings=[Opening(id="fn", area_m2=2.0, orientation=Orientation.N)],
        ),
    ]
    return Building(id="x", rooms=rooms)


def test_render_plan_png_is_png() -> None:
    png = render_plan_png(_building())
    assert png[:8] == b"\x89PNG\r\n\x1a\n"  # signature PNG
    assert len(png) > 1000


def test_render_plan_data_uri() -> None:
    uri = render_plan_data_uri(_building())
    assert uri.startswith("data:image/png;base64,")


def test_zone_results_have_seasonal_and_co2() -> None:
    r = simulate_5r1c(_building(), synthetic_climate(), R5C1Params())
    assert len(r.zones) == 2
    for z in r.zones:
        assert z.label is not None and z.area_m2 is not None
        assert z.winter_min_c is not None and z.summer_max_c is not None
        assert z.co2_mean_ppm is not None and z.co2_max_ppm is not None
        # Été ≥ hiver ; CO₂ dans une plage physique ; max ≥ moyenne.
        assert z.summer_max_c >= z.winter_min_c
        assert 400 <= z.co2_mean_ppm <= 5000
        assert z.co2_max_ppm >= z.co2_mean_ppm


def test_south_room_overheats_more_than_north() -> None:
    """Sanité : la pièce sud/est surchauffe plus que la chambre nord."""
    r = simulate_5r1c(_building(), synthetic_climate())
    by_id = {z.zone_id: z for z in r.zones}
    sejour, chambre = by_id["sejour"].summer_max_c, by_id["chambre"].summer_max_c
    assert sejour is not None and chambre is not None
    assert sejour >= chambre
