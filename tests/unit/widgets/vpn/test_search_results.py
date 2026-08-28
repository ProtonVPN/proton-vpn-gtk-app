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
from unittest.mock import Mock

from proton.vpn.session.servers import LogicalServer, TierEnum

from proton.vpn.app.gtk.controller import Controller
from proton.vpn.app.gtk.widgets.vpn.search_results import SearchResults


def _make_server(name="US#1", tier=TierEnum.FREE, load=42):
    return LogicalServer({
        "ID": 1, "Name": name, "Status": 1, "Load": load,
        "Servers": [{"Status": 1}],
        "ExitCountry": "US", "EntryCountry": "US",
        "City": "New York", "Tier": tier,
    })


def _server_search(controller):
    search_results = SearchResults(controller)
    # pylint: disable=protected-access
    return search_results._filtered_country_list._servers


def test_search_results_omits_servers_from_search_when_server_selection_requires_upgrade():
    controller = Mock(spec=Controller)
    controller.server_selection_requires_upgrade = True
    controller.server_list = [_make_server()]

    assert list(_server_search(controller)("US")) == []


def test_search_results_includes_matching_servers_in_search_when_upgrade_is_not_required():
    controller = Mock(spec=Controller)
    controller.server_selection_requires_upgrade = False
    controller.user_tier = TierEnum.FREE
    controller.server_list = [_make_server()]

    assert list(_server_search(controller)("US")) == [("US#1", 42)]
