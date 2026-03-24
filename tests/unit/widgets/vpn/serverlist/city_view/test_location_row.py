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
from unittest.mock import Mock

import pytest

from proton.vpn.session.servers import Location, LogicalServer, TierEnum

from proton.vpn.app.gtk.controller import Controller
from proton.vpn.app.gtk.widgets.vpn.serverlist.city_view.location_row import LocationRow
from tests.unit.testing_utils import process_gtk_events

@pytest.fixture
def plus_and_free_servers():
    api_response = {
        "LogicalServers": [
            {
                "ID": 1,
                "Name": "JP#9",
                "Status": 1,
                "Load": 50,
                "Servers": [{"Status": 1}],
                "ExitCountry": "JP",
                "City": "Tokyo",
                "Tier": TierEnum.PLUS,

            },
            {
                "ID": 2,
                "Name": "JP-FREE#10",
                "Status": 1,
                "Load": 50,
                "Servers": [{"Status": 1}],
                "ExitCountry": "JP",
                "City": "Tokyo",
                "Tier": TierEnum.FREE,

            },
        ]
    }
    return [LogicalServer(server) for server in api_response["LogicalServers"]]


@pytest.mark.parametrize("user_tier, expected_servers", [
    (TierEnum.FREE, ["JP-FREE#10", "JP#9"]),
    (TierEnum.PLUS, ["JP#9", "JP-FREE#10"])
    ])
def test_location_row_displays_free_servers_first_to_free_users(
        user_tier, expected_servers, plus_and_free_servers
):
    """
    Free users should have free servers listed first.
    Plus users should have plus servers listed first.
    """
    location = Location(name="Tokyo", servers=plus_and_free_servers)
    location_row = LocationRow()

    location_row.display(Mock(spec=Controller), location, user_tier)
    location_row.click_toggle_button()

    process_gtk_events()
    assert len(location_row.server_rows) == 2
    assert location_row.server_rows[0].label == expected_servers[0]
    assert location_row.server_rows[1].label == expected_servers[1]


@pytest.fixture
def free_and_plus_servers():
    """Same servers as plus_and_free_servers but with free server first in the list."""
    api_response = {
        "LogicalServers": [
            {
                "ID": 2,
                "Name": "JP-FREE#10",
                "Status": 1,
                "Load": 50,
                "Servers": [{"Status": 1}],
                "ExitCountry": "JP",
                "City": "Tokyo",
                "Tier": TierEnum.FREE,

            },
            {
                "ID": 1,
                "Name": "JP#9",
                "Status": 1,
                "Load": 50,
                "Servers": [{"Status": 1}],
                "ExitCountry": "JP",
                "City": "Tokyo",
                "Tier": TierEnum.PLUS,

            },
        ]
    }
    return [LogicalServer(server) for server in api_response["LogicalServers"]]


def test_location_row_displays_paid_servers_first_to_paid_users(free_and_plus_servers):
    """Paid users (e.g. Plus tier) should have paid servers listed first."""
    location = Location(name="Tokyo", servers=free_and_plus_servers)
    location_row = LocationRow()

    location_row.display(Mock(spec=Controller), location, TierEnum.PLUS)
    location_row.click_toggle_button()

    process_gtk_events()
    assert len(location_row.server_rows) == 2
    assert location_row.server_rows[0].label == "JP#9"
    assert location_row.server_rows[1].label == "JP-FREE#10"


def test_display_shows_the_row_in_expanded_state_when_specified(plus_and_free_servers):
    location = Location(name="Tokyo", servers=plus_and_free_servers)
    location_row = LocationRow()
    mock_controller = Mock(spec=Controller)

    # Display the city row in expanded state
    location_row.display(mock_controller, location, TierEnum.PLUS, expanded=True)
    process_gtk_events()

    assert location_row.expanded, "Location row should remain expanded after refresh"
    assert len(location_row.server_rows) == 2, "Servers should still be visible"