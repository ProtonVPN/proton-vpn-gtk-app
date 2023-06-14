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
from time import time
from unittest.mock import Mock

from gi.repository import GLib
import pytest

from proton.vpn.session.servers import ServerList, LogicalServer

from proton.vpn.app.gtk.widgets.vpn.search_entry import SearchEntry
from proton.vpn.app.gtk.widgets.vpn.serverlist.serverlist import ServerListWidget
from tests.unit.testing_utils import process_gtk_events, run_main_loop

PLUS_TIER = 2
FREE_TIER = 0

@pytest.fixture
def api_data():
    return {
        "Code": 1000,
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
        ]
    }


@pytest.fixture
def server_list(api_data):
    return ServerList(
        user_tier=PLUS_TIER,
        logicals=[LogicalServer(server) for server in api_data["LogicalServers"]]
    )


@pytest.fixture
def server_list_widget(server_list):
    server_list_widget = ServerListWidget(controller=Mock())
    server_list_widget.display(user_tier=PLUS_TIER, server_list=server_list)
    process_gtk_events()
    return server_list_widget


def test_search_shows_matching_server_row_and_its_country_when_searching_for_a_server_name(server_list_widget):
    search_widget = SearchEntry(server_list_widget)

    main_loop = GLib.MainLoop()

    # Changing the search widget text triggers the search.
    GLib.idle_add(search_widget.set_text, "jp-free#10")

    search_widget.connect("search-complete", lambda _: main_loop.quit())

    run_main_loop(main_loop)

    for country_row in server_list_widget.country_rows:
        expected_country_match = (country_row.country_name == "Japan")
        assert country_row.get_visible() is expected_country_match, \
            f"{country_row.country_name} did not have the expected visibility."

        # As our test search only matches a server name, the country row
        # containing it should be displayed expanded (rather than collapsed):
        assert country_row.showing_servers is expected_country_match, \
            f"{country_row.country_name} should be displayed " \
            f"{'expanded' if expected_country_match else 'collapsed'}"

        for server_row in country_row.server_rows:
            expected_server_match = (server_row.server_label == "JP-FREE#10")
            assert server_row.get_visible() is expected_server_match


def test_search_shows_matching_country_with_servers_collapsed_when_search_only_matches_country_name(server_list_widget):
    search_widget = SearchEntry(server_list_widget)

    main_loop = GLib.MainLoop()

    # Changing the search widget text triggers the search.
    GLib.idle_add(search_widget.set_text, "argentina")

    search_widget.connect("search-complete", lambda _: main_loop.quit())

    run_main_loop(main_loop)

    for country_row in server_list_widget.country_rows:
        expected_country_visible = (country_row.country_name == "Argentina")
        assert country_row.get_visible() is expected_country_visible, \
            f"{country_row.country_name} did not have the expected visibility."

        # Servers should be collapsed, as the search text does not match any.
        assert not country_row.showing_servers

        # Servers belonging to the country matched by the search text should
        # be flagged "visible", meaning that **if the country row is expanded**
        # then the user will see them.
        for server_row in country_row.server_rows:
            assert server_row.get_visible() is expected_country_visible


def test_search_does_not_show_any_countries_nor_servers_when_search_does_not_match_anything(server_list_widget):
    search_widget = SearchEntry(server_list_widget)

    main_loop = GLib.MainLoop()

    # Changing the search widget text triggers the search.
    GLib.idle_add(search_widget.set_text, "foobar")

    search_widget.connect("search-complete", lambda _: main_loop.quit())

    run_main_loop(main_loop)

    for country_row in server_list_widget.country_rows:
        assert not country_row.get_visible()
