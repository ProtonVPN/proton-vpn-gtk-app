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

from proton.vpn.session.servers import City, LogicalServer, TierEnum

from proton.vpn.app.gtk.controller import Controller
from proton.vpn.app.gtk.widgets.vpn.serverlist.city_view.city import CityRow
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
def test_city_row_shows_user_tier_cities_first_when_toggled(
        user_tier, expected_servers, free_and_plus_servers
):
    """
    Free users should have free servers listed first.
    Plus users should have plus servers listed first.
    """
    city = City(name="Tokyo", servers=free_and_plus_servers)
    city_row = CityRow()

    city_row.display(Mock(spec=Controller), city, user_tier)
    city_row.click_toggle_button()

    process_gtk_events()
    assert len(city_row.server_rows) == 2
    assert city_row.server_rows[0].label == expected_servers[0]
    assert city_row.server_rows[1].label == expected_servers[1]