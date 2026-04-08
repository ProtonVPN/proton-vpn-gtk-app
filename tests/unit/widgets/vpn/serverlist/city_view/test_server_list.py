"""
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
import time
from unittest.mock import Mock

import pytest
from proton.vpn.session.servers import ServerList

from proton.vpn.app.gtk.widgets.vpn.serverlist.city_view.serverlist import ServerListWidget
from tests.unit.testing_utils import process_gtk_events


PLUS_TIER = 2
FREE_TIER = 0

SERVER_LIST_TIMESTAMP = time.time()


@pytest.fixture
def unsorted_server_list():
    return ServerList.from_dict({
        "LogicalServers": [
            {
                "ID": 2,
                "Name": "AR#10",
                "Status": 1,
                "Load": 50,
                "Servers": [{"Status": 1}],
                "ExitCountry": "AR",
                "Tier": PLUS_TIER,
            },
            {
                "ID": 1,
                "Name": "JP-FREE#10",
                "Status": 1,
                "Load": 50,
                "Servers": [{"Status": 1}],
                "ExitCountry": "JP",
                "Tier": FREE_TIER,

            },
            {
                "ID": 3,
                "Name": "AR#9",
                "Status": 1,
                "Load": 50,
                "Servers": [{"Status": 1}],
                "ExitCountry": "AR",
                "Tier": PLUS_TIER,
            },
            {
                "ID": 5,
                "Name": "CH-JP#1",
                "Status": 1,
                "Load": 50,
                "Servers": [{"Status": 1}],
                "Features": 1,  # Secure core feature
                "EntryCountry": "CH",
                "ExitCountry": "JP",
                "Tier": PLUS_TIER,
            },
            {
                "ID": 4,
                "Name": "JP#9",
                "Status": 1,
                "Load": 50,
                "Servers": [{"Status": 1}],
                "ExitCountry": "JP",
                "Tier": PLUS_TIER,

            },
        ],
        "MaxTier": PLUS_TIER
    })


SERVER_LIST = ServerList.from_dict({
    "LogicalServers": [
        {
            "ID": 1,
            "Name": "AR#1",
            "Status": 1,
            "Load": 50,
            "Servers": [{"Status": 1}],
            "ExitCountry": "AR",
            "Tier": PLUS_TIER,
        },
        {
            "ID": 2,
            "Name": "AR#2",
            "Status": 1,
            "Load": 50,
            "Servers": [{"Status": 1}],
            "ExitCountry": "AR",
            "Tier": PLUS_TIER,
        },
    ],
    "MaxTier": PLUS_TIER
})


SERVER_LIST_UPDATED = ServerList.from_dict({
    "LogicalServers": [
        {
            "ID": 1,
            "Name": "Server Name Updated",
            "Status": 1,
            "Load": 51,
            "Servers": [{"Status": 1}],
            "ExitCountry": "AR",
            "Tier": PLUS_TIER,

        },
        {
            "ID": 2,
            "Name": "JP-FREE#10",
            "Status": 1,
            "Load": 52,
            "Servers": [{"Status": 1}],
            "ExitCountry": "JP",
            "Tier": FREE_TIER,

        },
    ],
    "MaxTier": PLUS_TIER
})


SERVER_LIST_WITH_CITIES = ServerList.from_dict({
    "LogicalServers": [
        {
            "ID": 1, "Name": "JP#1", "Status": 1, "Load": 50,
            "Servers": [{"Status": 1}], "ExitCountry": "JP",
            "City": "Tokyo", "Tier": PLUS_TIER,
        },
        {
            "ID": 2, "Name": "JP#2", "Status": 1, "Load": 50,
            "Servers": [{"Status": 1}], "ExitCountry": "JP",
            "City": "Osaka", "Tier": PLUS_TIER,
        },
    ],
    "MaxTier": PLUS_TIER
})


def _displayed_widget(server_list=SERVER_LIST_WITH_CITIES, user_tier=PLUS_TIER):
    widget = ServerListWidget(controller=Mock())
    widget.display(user_tier=user_tier, server_list=server_list)
    process_gtk_events()
    return widget


def test_focus_on_entry_connects_directly_when_name_contains_hash():
    mock_controller = Mock()
    widget = ServerListWidget(controller=mock_controller)
    widget.display(user_tier=PLUS_TIER, server_list=SERVER_LIST_WITH_CITIES)

    widget.focus_on_entry(None, "JP#1")

    mock_controller.connect_to_server.assert_called_once_with("JP#1")


def test_focus_on_entry_focuses_country_row_when_name_matches_country():
    widget = _displayed_widget()
    country_row = widget.country_rows[0]
    country_row.grab_focus = Mock()

    widget.focus_on_entry(None, "Japan")

    country_row.grab_focus.assert_called_once()


def test_focus_on_entry_focuses_location_when_name_matches_city():
    widget = _displayed_widget()
    country_row = widget.country_rows[0]
    country_row.click_toggle_button()
    process_gtk_events()
    location_row = next(r for r in country_row.location_rows if r.label == "Tokyo")
    location_row.grab_focus = Mock()

    widget.focus_on_entry(None, "Tokyo")

    location_row.grab_focus.assert_called_once()


def test_server_list_widget_subscribes_to_server_list_updates_on_realize():
    mock_controller = Mock()

    server_list_widget = ServerListWidget(
        controller=mock_controller
    )
    server_list_widget.display(user_tier=PLUS_TIER, server_list=SERVER_LIST)

    # Assert that we only have servers in one country.
    assert len(server_list_widget.country_rows) == 1

    # Simulate new-server-list signal.
    mock_controller.server_list = SERVER_LIST_UPDATED
    server_list_updated_callback = mock_controller.set_server_list_updated_callback.call_args[0][0]
    server_list_updated_callback()

    process_gtk_events()

    # Assert that we now have servers in two countries.
    assert len(server_list_widget.country_rows) == 2


def test_unload_disconnects_from_server_list_updates_and_removes_country_rows():
    mock_controller = Mock()
    server_list_widget = ServerListWidget(
        controller=mock_controller
    )

    server_list_widget.display(user_tier=PLUS_TIER, server_list=SERVER_LIST)

    assert len(server_list_widget.country_rows) == 1

    server_list_widget.unload()

    # Assert that server list/loads update callbacks were unset
    mock_controller.unset_server_list_updated_callback.assert_called_once()
    mock_controller.unset_server_loads_updated_callback.assert_called_once()


@pytest.mark.parametrize(
    "user_tier,expected_country_names", [
        (FREE_TIER, ["Japan", "Argentina"]),
        (PLUS_TIER, ["Argentina", "Japan"])
    ]
)
def test_server_list_widget_orders_country_rows_depending_on_user_tier(
        user_tier, expected_country_names, unsorted_server_list
):
    """
    Plus users should see countries sorted alphabetically.
    Free users, apart from having countries sorted alphabetically, should see
    countries having free servers first.
    """
    servers_widget = ServerListWidget(
        controller=Mock(),
    )

    servers_widget.display(
        user_tier=user_tier,
        server_list=unsorted_server_list
    )

    country_names = [country_row.country_name for country_row in servers_widget.country_rows]
    assert country_names == expected_country_names
