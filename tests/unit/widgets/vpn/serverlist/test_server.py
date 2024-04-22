"""
Copyright (c) 2023 Proton AG

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
from typing import Callable
from unittest.mock import Mock
import pytest

from gi.repository import GLib

from proton.vpn.core.session.servers import LogicalServer
from proton.vpn.core.session.servers.types import ServerLoad

from proton.vpn.app.gtk import Gtk
from proton.vpn.app.gtk.controller import Controller
from proton.vpn.app.gtk.widgets.vpn.serverlist.icons import P2PIcon, StreamingIcon, \
    SmartRoutingIcon, TORIcon, SecureCoreIcon
from proton.vpn.app.gtk.widgets.vpn.serverlist.server import ServerRow

from tests.unit.testing_utils import process_gtk_events, run_main_loop

FREE_TIER = 0
PLUS_TIER = 2


@pytest.fixture
def plus_logical_server():
    return LogicalServer(data={
        "ID": "1",
        "Name": "IS#1",
        "Status": 1,
        "Load": 50,
        "Servers": [
            {
                "ID": "OYB-3pMQQA2Z2Qnp5s5nIvTV…x9DCAUM9uXfM2ZUFjzPXw==",
                "Status": 1
            }
        ],
        "Tier": PLUS_TIER,
    })


@pytest.fixture
def mock_controller():
    return Mock(Controller)


def test_server_row_displays_server_name(
        plus_logical_server, mock_controller
):
    server_row = ServerRow(
        server=plus_logical_server, user_tier=PLUS_TIER, controller=mock_controller
    )

    assert server_row.server_label == "IS#1"


@pytest.fixture
def unavailable_logical_server():
    return LogicalServer(data={
        "Name": "IS#1",
        "Status": 0,
        "Servers": [],
        "Tier": PLUS_TIER,
    })


def test_server_row_signals_server_under_maintenance(
        unavailable_logical_server, mock_controller
):
    server_row = ServerRow(
        server=unavailable_logical_server, user_tier=PLUS_TIER, controller=mock_controller
    )

    def assertions():
        assert server_row.under_maintenance_icon_visible

    run_in_window(server_row, assertions)


@pytest.fixture
def logical_server_with_features():
    return LogicalServer(data={
        "ID": "1",
        "Name": "IS#1",
        "Status": 1,
        "Load": 50,
        "Servers": [{"ID": "1", "Status": 1}],
        "Features": 14,  # 2 (TOR) + 4 (P2P) + 8 (Streaming)
        "Tier": PLUS_TIER,
        "HostCountry": "us"  # smart routing is enabled when host country is not None
    })


def test_server_row_displays_server_feature_icons(mock_controller, logical_server_with_features):
    server_row = ServerRow(server=logical_server_with_features, user_tier=PLUS_TIER, controller=mock_controller)

    def assertions():
        assert server_row.is_server_feature_icon_displayed(SmartRoutingIcon)
        assert server_row.is_server_feature_icon_displayed(P2PIcon)
        assert server_row.is_server_feature_icon_displayed(TORIcon)
        assert server_row.is_server_feature_icon_displayed(StreamingIcon)

    run_in_window(server_row, assertions)


@pytest.fixture
def logical_server_with_secure_core():
    return LogicalServer(data={
        "ID": "1",
        "Name": "CH-JP#1",
        "Status": 1,
        "Load": 50,
        "Servers": [{"ID": "1", "Status": 1}],
        "Features": 13,  # 1 (Secure core) + 4 (P2P) + 8 (Streaming)
        "Tier": PLUS_TIER,
        "HostCountry": "us",  # smart routing is enabled when host country is not None
        "EntryCountry": "CH",
        "ExitCountry": "JP",
    })


def test_server_row_only_displays_secure_core_icon(mock_controller, logical_server_with_secure_core):
    server_row = ServerRow(server=logical_server_with_secure_core, user_tier=PLUS_TIER, controller=mock_controller)

    def assertions():
        assert server_row.is_server_feature_icon_displayed(SecureCoreIcon)
        assert not server_row.is_server_feature_icon_displayed(P2PIcon)
        assert not server_row.is_server_feature_icon_displayed(StreamingIcon)
        assert not server_row.is_server_feature_icon_displayed(SmartRoutingIcon)

    run_in_window(server_row, assertions)


def test_connect_button_click_triggers_vpn_connection(plus_logical_server, mock_controller):
    server_row = ServerRow(
        server=plus_logical_server, user_tier=PLUS_TIER, controller=mock_controller
    )

    server_row.click_connect_button()

    process_gtk_events()

    mock_controller.connect_to_server.assert_called_once_with(
        plus_logical_server.name
    )


def test_update_server_load(plus_logical_server):
    server_row = ServerRow(server=plus_logical_server, user_tier=PLUS_TIER, controller=Mock())
    server_update = ServerLoad(data={
        "ID": "1",
        "Name": "IS#1",
        "Status": 1,
        "Load": 51,
    })

    def assertions():
        assert server_row.server_load_label == "50%"

        plus_logical_server.update(server_update)
        server_row.update_server_load()

        assert server_row.server_load_label == "51%"

    run_in_window(server_row, assertions)


def test_update_server_load_should_also_change_maintenance_status_if_needed(plus_logical_server):
    server_row = ServerRow(server=plus_logical_server, user_tier=PLUS_TIER, controller=Mock())
    server_update = ServerLoad(data={
        "ID": "1",
        "Name": "IS#1",
        "Status": 0,
        "Load": 50,
    })

    def assertions():
        assert server_row.is_connect_button_visible
        assert not server_row.under_maintenance_icon_visible

        plus_logical_server.update(server_update)
        server_row.update_server_load()

        assert not server_row.is_connect_button_visible
        assert server_row.under_maintenance_icon_visible

    run_in_window(server_row, assertions)


def run_in_window(server_row: ServerRow, assertions: Callable):
    """Adds the server row to a Gtk.Window, launches it,
    calls the assertions and closes it."""
    window = Gtk.Window()
    window.add(server_row)
    main_loop = GLib.MainLoop()

    def on_show(_):
        try:
            assertions()
        finally:
            main_loop.quit()

    window.connect("show", on_show)
    GLib.idle_add(window.show_all)

    run_main_loop(main_loop)

