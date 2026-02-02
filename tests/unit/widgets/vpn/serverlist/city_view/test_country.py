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
from proton.vpn.app.gtk.widgets.vpn.serverlist.city_view.country import CountryRow
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
        ]
    }
    return [LogicalServer(server) for server in api_response["LogicalServers"]]


@pytest.mark.parametrize("user_tier, expected_cities", [
    (TierEnum.FREE, ["Tokyo", "Osaka"]),
    (TierEnum.PLUS, ["Osaka", "Tokyo"])
    ])
def test_country_row_shows_user_tier_cities_first_when_toggled(
        user_tier, expected_cities, free_and_plus_servers
):
    """
    Free users should have free cities listed first.
    Plus users should have plus cities listed first.
    """
    country = Country(code="jp", servers=free_and_plus_servers)
    country_row = CountryRow()

    country_row.display(Mock(spec=Controller), country, user_tier)
    country_row.click_toggle_button()

    process_gtk_events()
    assert len(country_row.city_rows) == 2
    assert country_row.city_rows[0].label == expected_cities[0]
    assert country_row.city_rows[1].label == expected_cities[1]
