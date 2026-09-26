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
from proton.vpn.session.servers.types import ServerLoad

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


@pytest.fixture
def free_server():
    api_response = {
        "LogicalServers": [
            {
                "ID": 1,
                "Name": "JP-FREE#1",
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


def test_free_location_is_connectable_for_free_user_when_server_selection_does_not_require_upgrade(
    free_server
):
    """Current behavior: a free-tier user can connect to a location/server that's free."""
    location = Location(name="Tokyo", servers=free_server)
    location_row = LocationRow()
    mock_controller = Mock(spec=Controller)
    mock_controller.server_selection_requires_upgrade = False

    location_row.display(mock_controller, location, TierEnum.FREE, expanded=True)
    process_gtk_events()

    assert location_row.row_content.label_sensitive is True
    assert location_row.server_rows[0].label_sensitive is True


def test_free_location_requires_upgrade_for_free_user_when_server_selection_requires_upgrade(
    free_server
):
    """New behavior: only country rows are connectable for free-tier users, regardless
    of whether the location/server is itself free."""
    location = Location(name="Tokyo", servers=free_server)
    location_row = LocationRow()
    mock_controller = Mock(spec=Controller)
    mock_controller.server_selection_requires_upgrade = True

    location_row.display(mock_controller, location, TierEnum.FREE, expanded=True)
    process_gtk_events()

    assert location_row.row_content.label_sensitive is False
    assert location_row.server_rows[0].label_sensitive is False


@pytest.mark.parametrize("user_tier", [TierEnum.FREE, TierEnum.PLUS])
def test_location_row_update_server_loads_updates_displayed_loads_in_place(
        user_tier, plus_and_free_servers
):
    """Loads updates mutate the server models the rows already reference, so
    the built server rows just re-read them (in both display orderings)."""
    location = Location(name="Tokyo", servers=plus_and_free_servers)
    location_row = LocationRow()
    location_row.display(Mock(spec=Controller), location, user_tier, expanded=True)
    process_gtk_events()
    assert len(location_row.server_rows) == 2

    for logical in location.servers:
        new_load = 25 if logical.name == "JP#9" else 75
        logical.update(ServerLoad({
            "ID": logical.id, "Load": new_load, "Score": 1, "Status": 1,
        }))

    assert location_row.update_server_loads() is False

    loads_by_label = {row.label: row.server_load for row in location_row.server_rows}
    assert loads_by_label == {"JP#9": "25%", "JP-FREE#10": "75%"}
    assert len(location_row.server_rows) == 2


def test_location_row_update_server_loads_is_a_no_op_for_collapsed_rows(
        plus_and_free_servers
):
    location = Location(name="Tokyo", servers=plus_and_free_servers)
    location_row = LocationRow()

    location_row.display(Mock(spec=Controller), location, TierEnum.PLUS)
    process_gtk_events()

    assert location_row.server_rows == []
    assert location_row.update_server_loads() is False


def test_location_row_update_server_loads_returns_true_when_a_server_goes_under_maintenance(
        plus_and_free_servers
):
    location = Location(name="Tokyo", servers=plus_and_free_servers)
    location_row = LocationRow()
    location_row.display(Mock(spec=Controller), location, TierEnum.PLUS, expanded=True)
    process_gtk_events()
    rows_by_label = {row.label: row for row in location_row.server_rows}

    jp_free = next(
        logical for logical in location.servers if logical.name == "JP-FREE#10"
    )
    jp_free.update(ServerLoad({"ID": jp_free.id, "Load": 75, "Score": 1, "Status": 0}))

    assert location_row.update_server_loads() is True

    # The restyle is not done in place: the row is left as it was displayed.
    assert not rows_by_label["JP-FREE#10"].under_maintenance_icon.get_visible()
    assert rows_by_label["JP-FREE#10"].server_load == "50%"


def test_location_row_update_server_loads_falls_back_when_rows_are_out_of_sync(
        plus_and_free_servers
):
    location = Location(name="Tokyo", servers=plus_and_free_servers)
    location_row = LocationRow()
    location_row.display(Mock(spec=Controller), location, TierEnum.PLUS, expanded=True)
    process_gtk_events()
    rows_by_label = {row.label: row for row in location_row.server_rows}

    # Simulate a desync between the built rows and the server models.
    location_row._server_rows.pop()

    assert location_row.update_server_loads() is True
    # No row was touched before the fallback was requested.
    assert rows_by_label["JP#9"].server_load == "50%"