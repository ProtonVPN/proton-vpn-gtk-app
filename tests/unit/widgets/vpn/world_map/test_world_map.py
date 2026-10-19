"""
Tests for the world map widget.


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
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from proton.vpn.connection import states

from proton.vpn.app.gtk import Gtk
from proton.vpn.app.gtk.widgets.vpn.world_map import world_map as world_map_module
from proton.vpn.app.gtk.widgets.vpn.world_map.geometry import load_shapes
from proton.vpn.app.gtk.widgets.vpn.world_map.world_map import WorldMap
from tests.unit.testing_utils import process_gtk_events

PLUS_TIER = 2


def server(name, exit_country):
    return SimpleNamespace(
        id=name, name=name, exit_country=exit_country, free=False, under_maintenance=False
    )


@pytest.fixture
def servers():
    return [server("US-TX#1", "US"), server("US-NY#1", "US"), server("FR#1", "FR")]


@pytest.fixture
def server_list(servers):
    countries = [
        SimpleNamespace(
            code=code, free=False, under_maintenance=False,
            locations=[SimpleNamespace(servers=[s for s in servers if s.exit_country == code])]
        )
        for code in ("US", "FR")
    ]
    return SimpleNamespace(
        group_by_country=lambda **_: countries,
        get_by_id=lambda server_id: next(s for s in servers if s.id == server_id),
    )


@pytest.fixture
def controller():
    controller = Mock()
    controller.server_selection_requires_upgrade = False
    return controller


@pytest.fixture
def connect_callbacks(monkeypatch):
    """Records what the map connects to, instead of connecting."""
    connections = []
    monkeypatch.setattr(
        world_map_module, "make_country_connect_callback",
        lambda _controller, code: lambda: connections.append(("country", code))
    )
    monkeypatch.setattr(
        world_map_module, "make_connect_callback",
        lambda _controller, servers, _tier: lambda: connections.append(
            ("servers", [s.name for s in servers])
        )
    )
    return connections


@pytest.fixture
def world_map(controller, server_list, connect_callbacks):  # pylint: disable=unused-argument
    world_map = WorldMap(controller)
    window = Gtk.Window()
    window.set_default_size(450, 340)
    window.set_child(world_map)
    window.present()
    process_gtk_events()
    world_map.display(PLUS_TIER, server_list)
    yield world_map
    window.destroy()


def position_of(world_map, region_key):
    """Widget position of the shape of a region."""
    shape = next(s for s in load_shapes() if s.key == region_key)
    lon, lat = {
        "US-TX": (-99, 31), "US-NY": (-75.5, 43), "FR": (2.3, 47), "US-WY": (-107.5, 43),
    }[shape.key]
    return world_map._viewport.to_screen(lon, lat)  # pylint: disable=protected-access


def popover_buttons(world_map):
    box = world_map._popover.get_child()  # pylint: disable=protected-access
    buttons, child = [], box.get_first_child()
    while child:
        if isinstance(child, Gtk.Button):
            buttons.append(child)
        child = child.get_next_sibling()
    return buttons


def test_hovering_a_us_state_shows_its_name(world_map):
    world_map._on_motion(None, *position_of(world_map, "US-TX"))  # pylint: disable=protected-access

    assert "Texas" in world_map.get_tooltip_text()


def test_hovering_a_country_without_servers_shows_nothing(world_map):
    # Canada is on the map but not in the server list.
    x, y = world_map._viewport.to_screen(-100, 60)  # pylint: disable=protected-access

    world_map._on_motion(None, x, y)  # pylint: disable=protected-access

    assert world_map.get_tooltip_text() is None


def test_clicking_a_us_state_offers_to_connect_to_it_or_to_the_country(
    world_map, connect_callbacks
):
    x, y = position_of(world_map, "US-TX")

    world_map._on_click(None, 1, x, y)  # pylint: disable=protected-access
    buttons = popover_buttons(world_map)

    assert [button.get_label() for button in buttons][0] == "Connect"
    assert len(buttons) == 2
    buttons[0].emit("clicked")
    assert connect_callbacks == [("servers", ["US-TX#1"])]


def test_clicking_a_state_without_servers_only_offers_to_connect_to_the_country(
    world_map, connect_callbacks
):
    x, y = position_of(world_map, "US-WY")

    world_map._on_click(None, 1, x, y)  # pylint: disable=protected-access
    buttons = popover_buttons(world_map)

    assert len(buttons) == 1
    buttons[0].emit("clicked")
    assert connect_callbacks == [("country", "US")]


def test_clicking_a_country_connects_to_it(world_map, connect_callbacks):
    x, y = position_of(world_map, "FR")

    world_map._on_click(None, 1, x, y)  # pylint: disable=protected-access
    popover_buttons(world_map)[0].emit("clicked")

    assert connect_callbacks == [("country", "FR")]


def test_dragging_the_map_does_not_click(world_map):
    x, y = position_of(world_map, "FR")
    world_map._on_drag_begin(None, x, y)  # pylint: disable=protected-access
    world_map._on_drag_update(None, 30, 30)  # pylint: disable=protected-access

    world_map._on_click(None, 1, x, y)  # pylint: disable=protected-access

    assert not world_map._popover.get_visible()  # pylint: disable=protected-access


def test_the_connected_state_offers_to_disconnect(world_map, controller):
    state = states.Connected()
    state.context = SimpleNamespace(connection=SimpleNamespace(server_id="US-TX#1"))
    world_map.connection_status_update(state)
    x, y = position_of(world_map, "US-TX")

    world_map._on_click(None, 1, x, y)  # pylint: disable=protected-access
    buttons = popover_buttons(world_map)
    buttons[0].emit("clicked")

    assert buttons[0].get_label() == "Disconnect"
    controller.disconnect.assert_called_once()


def test_scrolling_zooms_the_map(world_map):
    world_map._on_motion(None, 200, 100)  # pylint: disable=protected-access

    world_map._on_scroll(None, 0, -1)  # pylint: disable=protected-access

    assert world_map._viewport.zoom > 1  # pylint: disable=protected-access
