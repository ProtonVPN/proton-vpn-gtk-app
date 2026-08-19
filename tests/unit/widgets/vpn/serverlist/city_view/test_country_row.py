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

from proton.vpn.session.servers import Country, LogicalServer, TierEnum

from proton.vpn.app.gtk.controller import Controller
from proton.vpn.app.gtk.widgets.vpn.serverlist.city_view.country_row import CountryRow
from tests.unit.testing_utils import process_gtk_events

@pytest.fixture
def free_and_plus_servers():
    api_response = {
        "LogicalServers": [
            {
                "ID": 1,
                "Name": "JP#9",
                "Status": 1,
                "Load": 50,
                "Servers": [{"Status": 1}],
                "ExitCountry": "JP",
                "City": "Osaka",
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
            {
                "ID": 3,
                "Name": "JP-FREE#11",
                "Status": 1,
                "Load": 51,
                "Servers": [{"Status": 1}],
                "ExitCountry": "JP",
                "City": "Tokyo",
                "Tier": TierEnum.PLUS,

            },
        ]
    }
    return [LogicalServer(server) for server in api_response["LogicalServers"]]


@pytest.mark.parametrize("user_tier, expected_cities", [
    (TierEnum.FREE, ["Tokyo", "Osaka"]),
    (TierEnum.PLUS, ["Osaka", "Tokyo"])
    ])
def test_country_row_shows_free_locations_first_when_toggled(
        user_tier, expected_cities, free_and_plus_servers
):
    """
    Free users should have free locations listed first.
    Plus users should have locations listed in alphabetical order.
    """
    country = Country(code="jp", servers=free_and_plus_servers, group_by_location=True)
    country_row = CountryRow()

    country_row.display(Mock(spec=Controller), country, user_tier)
    country_row.click_toggle_button()

    process_gtk_events()
    assert len(country_row.location_rows) == 2
    assert country_row.location_rows[0].label == expected_cities[0]
    assert country_row.location_rows[1].label == expected_cities[1]


def test_display_shows_the_row_in_expanded_state_when_specified(free_and_plus_servers):
    country = Country(code="jp", servers=free_and_plus_servers, group_by_location=True)
    country_row = CountryRow()
    mock_controller = Mock(spec=Controller)

    # Collect expanded cities before refresh (set of lowercase city names)
    expanded_groups = {"tokyo", "osaka"}

    # Display the country row in expanded state, with expanded cities
    country_row.display(
        mock_controller, country, TierEnum.PLUS,
        expanded=True, expanded_groups=expanded_groups
    )
    process_gtk_events()

    assert country_row.expanded, "Country should remain expanded after refresh"
    assert all(city_row.expanded for city_row in country_row.location_rows), "All cities should be expanded"


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


@pytest.fixture
def paid_server():
    api_response = {
        "LogicalServers": [
            {
                "ID": 1,
                "Name": "JP#1",
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


def test_paid_country_requires_upgrade_for_free_user(paid_server):
    """A paid country requires upgrade for a free-tier user."""
    country = Country(code="jp", servers=paid_server, group_by_location=True)
    country_row = CountryRow()
    mock_controller = Mock(spec=Controller)
    mock_controller.feature_flags.get.return_value = False

    country_row.display(mock_controller, country, TierEnum.FREE)
    process_gtk_events()

    assert country_row.row_content.label_sensitive is False


@pytest.mark.parametrize("free_rescope_enabled", [False, True])
def test_free_country_connectability_is_invariant_to_free_rescope_flag(
    free_server, free_rescope_enabled
):
    """A free country stays connectable for a free-tier user regardless of the
    FreeRescope flag"""
    country = Country(code="jp", servers=free_server, group_by_location=True)
    country_row = CountryRow()
    mock_controller = Mock(spec=Controller)
    mock_controller.feature_flags.get.return_value = free_rescope_enabled

    country_row.display(mock_controller, country, TierEnum.FREE)
    process_gtk_events()

    assert country_row.row_content.label_sensitive is True
