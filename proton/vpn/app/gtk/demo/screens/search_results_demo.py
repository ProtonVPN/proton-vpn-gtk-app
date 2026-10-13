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


Demo factories for the server search results.
"""
from proton.vpn.session.servers import ServerList

from proton.vpn.app.gtk import Gtk
from proton.vpn.app.gtk.demo.framing import framed_like_app
from proton.vpn.app.gtk.demo.mocks import mock_controller
from proton.vpn.app.gtk.demo.registry import register_demo
from proton.vpn.app.gtk.widgets.vpn.search_results import SearchResults

SEARCH_TEXT = "ch"
PLUS_TIER = 2

# (name, country code, city, load): servers whose country, city or name
# contains SEARCH_TEXT, so each kind of result shows.
SERVERS = [
    ("LI#1", "LI", "Vaduz", 30),
    ("CZ#1", "CZ", "Prague", 40),
    ("CN#1", "CN", "Beijing", 50),
    ("CL#1", "CL", "Santiago", 60),
    ("TD#1", "TD", "N'Djamena", 70),
    ("RO#1", "RO", "Bucharest", 35),
    ("US#1", "US", "Chicago", 45),
    ("DE#1", "DE", "Munich", 55),
    ("CH#1", "CH", "Geneva", 23),
    ("CH#2", "CH", "Geneva", 67),
    ("CH#3", "CH", "Geneva", 91),
]


def _server_list() -> ServerList:
    return ServerList.from_dict({
        "LogicalServers": [
            {
                "ID": index, "Name": name, "Status": 1, "Load": load,
                "Servers": [{"Status": 1}], "EntryCountry": country,
                "ExitCountry": country, "City": city, "Tier": PLUS_TIER,
            }
            for index, (name, country, city, load) in enumerate(SERVERS)
        ],
        "MaxTier": PLUS_TIER,
    })


def _results_list(results: SearchResults) -> Gtk.TreeView:
    """The tree view inside the search results: scrolled window > viewport >
    box > tree view."""
    return results.get_child().get_child().get_first_child()


def _search(results: SearchResults, select_first_country: bool) -> None:
    results.on_search_changed(Gtk.SearchEntry(text=SEARCH_TEXT))
    if select_first_country:
        _results_list(results).get_selection().select_path(Gtk.TreePath.new_from_string("0:0"))


def _results(select_first_country: bool) -> Gtk.Widget:
    controller = mock_controller()
    controller.server_list = _server_list()
    controller.user_tier = PLUS_TIER
    controller.server_selection_requires_upgrade = False
    results = SearchResults(controller)
    _search(results, select_first_country)
    return framed_like_app(results)


@register_demo("search-results", label="results")
def search_results() -> Gtk.Widget:
    """Search results for "ch", nothing selected."""
    return _results(select_first_country=False)


@register_demo("search-results", label="row-selected")
def search_results_row_selected() -> Gtk.Widget:
    """Search results with a row selected (e.g. moving through them with the keyboard)."""
    return _results(select_first_country=True)
