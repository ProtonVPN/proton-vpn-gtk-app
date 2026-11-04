"""
Tests for the geometry of the world map.


Copyright (c) 2026 Proton AG

This file is part of Proton VPN.

Proton VPN is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Proton VPN is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with ProtonVPN.  If not, see <https://www.gnu.org/licenses/>.
"""
import pytest

from proton.vpn.app.gtk.widgets.vpn.world_map.geometry import (
    MAX_ZOOM, MIN_ZOOM, Viewport, hit_test, load_shapes, point_in_ring, project, unproject
)


@pytest.fixture
def viewport():
    viewport = Viewport()
    viewport.resize(1000, 600)
    return viewport


def test_unproject_is_the_inverse_of_project():
    lon, lat = unproject(*project(10.5, 48.2))

    assert lon == pytest.approx(10.5)
    assert lat == pytest.approx(48.2)


def test_point_in_ring():
    square = [(0, 0), (10, 0), (10, 10), (0, 10)]

    assert point_in_ring(5, 5, square)
    assert not point_in_ring(15, 5, square)
    assert not point_in_ring(5, -1, square)


def test_viewport_keeps_the_aspect_ratio_of_the_map(viewport):
    viewport.resize(1000, 2000)  # much higher than the map

    top_left = viewport.to_screen(-180, 84)
    bottom_right = viewport.to_screen(180, -57)

    assert bottom_right[0] - top_left[0] == pytest.approx(1000)
    assert top_left[1] > 0  # centered vertically, not stretched


def test_viewport_from_screen_is_the_inverse_of_to_screen(viewport):
    viewport.zoom_at(300, 200, 4)

    lon, lat = viewport.from_screen(*viewport.to_screen(2.35, 48.85))

    assert lon == pytest.approx(2.35)
    assert lat == pytest.approx(48.85)


def test_zooming_keeps_the_position_under_the_pointer_fixed(viewport):
    pointer = viewport.to_screen(10, 50)

    viewport.zoom_at(*pointer, 3)

    assert viewport.to_screen(10, 50) == pytest.approx(pointer, abs=1.0)


def test_zoom_is_limited(viewport):
    viewport.zoom_at(500, 300, 1000)
    assert viewport.zoom == MAX_ZOOM

    viewport.zoom_at(500, 300, 1 / 1000)
    assert viewport.zoom == MIN_ZOOM


def test_panning_cannot_move_the_map_away_from_the_widget(viewport):
    viewport.zoom_at(500, 300, 4)

    viewport.pan_by(100000, 100000)

    assert viewport.to_screen(-180, 84)[0] <= 0.001
    assert viewport.to_screen(-180, 84)[1] <= 0.001
    viewport.pan_by(-1000000, -1000000)
    assert viewport.to_screen(180, -57)[0] >= 999.999
    assert viewport.to_screen(180, -57)[1] >= 599.999


def test_shapes_use_proton_country_codes():
    countries = {shape.country_code for shape in load_shapes() if not shape.us_state}

    assert "UK" in countries
    assert "GB" not in countries
    assert {"FR", "NO", "SG"} <= countries  # SG is a dot


def test_united_states_are_split_in_states():
    shapes = load_shapes()
    states = {shape.us_state for shape in shapes if shape.us_state}

    assert len(states) == 51  # 50 states and DC
    assert {"TX", "CA", "DC"} <= states
    assert not [s for s in shapes if s.country_code == "US" and not s.us_state]


def test_shape_keys_are_unique():
    keys = [shape.key for shape in load_shapes()]

    assert len(keys) == len(set(keys))


@pytest.mark.parametrize("lon, lat, key", [
    (-99, 31, "US-TX"),
    (-2, 53, "UK"),
    (2.3, 47, "FR"),
    (103.82, 1.35, "SG"),
])
def test_hit_test_finds_the_shape_at_a_position(viewport, lon, lat, key):
    shape = hit_test(load_shapes(), viewport, *viewport.to_screen(lon, lat))

    assert shape.key == key


def test_hit_test_finds_nothing_in_the_ocean(viewport):
    assert hit_test(load_shapes(), viewport, *viewport.to_screen(-30, 30)) is None
