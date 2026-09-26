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

from proton.vpn.app.gtk.widgets.vpn.serverlist.city_view import serverlist as serverlist_module
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


SERVER_LIST_WITH_SECURE_CORE = ServerList.from_dict({
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
        {
            "ID": 3, "Name": "CH-JP#1", "Status": 1, "Load": 50,
            "Servers": [{"Status": 1}], "Features": 1,  # Secure core feature
            "EntryCountry": "CH", "ExitCountry": "JP", "City": "Zurich",
            "Tier": PLUS_TIER,
        },
    ],
    "MaxTier": PLUS_TIER
})


def _displayed_widget(server_list=SERVER_LIST_WITH_CITIES, user_tier=PLUS_TIER):
    widget = ServerListWidget(controller=Mock())
    widget.display(user_tier=user_tier, server_list=server_list)
    process_gtk_events()
    return widget


def test_server_list_widget_subscribes_to_server_list_updates_on_realize(monkeypatch):
    monkeypatch.setattr(serverlist_module, "REFRESH_DELAY_MS", 0)
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


def test_filter_hides_country_rows_not_matching_search_text(unsorted_server_list):
    widget = _displayed_widget(server_list=unsorted_server_list)

    widget.filter("Argentina")

    country_visibility = {
        row.country_name: row.get_visible() for row in widget.country_rows
    }
    assert country_visibility == {"Argentina": True, "Japan": False}


def test_filter_keeps_country_matched_by_name_collapsed():
    """Expanding a country matched only by its own name would build all its
    location rows, which is too expensive on broad queries."""
    widget = _displayed_widget()

    japan_row = widget.country_rows[0]
    widget.filter("Japan")

    assert japan_row.get_visible()
    assert not japan_row.expanded
    assert not japan_row.location_rows


def test_filter_expands_country_matched_via_child():
    widget = _displayed_widget()

    japan_row = widget.country_rows[0]
    widget.filter("Tokyo")

    assert japan_row.get_visible()
    assert japan_row.expanded
    assert japan_row.location_rows


def test_filter_shows_all_children_of_manually_expanded_country_matched_by_name():
    """A country the user had expanded stays expanded when matched by name,
    with all its children visible and unfiltered."""
    widget = _displayed_widget()

    japan_row = widget.country_rows[0]
    japan_row.click_toggle_button()
    process_gtk_events()
    widget.filter("Japan")

    location_visibility = {
        row.label: row.get_visible() for row in japan_row.location_rows
    }
    assert location_visibility == {"Tokyo": True, "Osaka": True}
    for location_row in japan_row.location_rows:
        assert all(row.get_visible() for row in location_row.server_rows)


def test_filter_hides_locations_not_matching_search_text():
    widget = _displayed_widget()

    japan_row = widget.country_rows[0]
    widget.filter("Tokyo")

    location_visibility = {
        row.label: row.get_visible() for row in japan_row.location_rows
    }
    assert location_visibility == {"Tokyo": True, "Osaka": False}


def test_filter_shows_location_matching_server_name():
    widget = _displayed_widget()

    japan_row = widget.country_rows[0]
    widget.filter("JP#2")

    location_visibility = {
        row.label: (row.get_visible(), row.expanded) for row in japan_row.location_rows
    }
    assert location_visibility == {"Tokyo": (False, False), "Osaka": (True, True)}

    osaka_row = next(row for row in japan_row.location_rows if row.label == "Osaka")
    server_visibility = {
        row.label: row.get_visible() for row in osaka_row.server_rows
    }
    assert server_visibility == {"JP#2": True}


def test_clearing_filter_restores_previous_state():
    widget = _displayed_widget()

    japan_row = widget.country_rows[0]
    japan_row.click_toggle_button()
    process_gtk_events()
    tokyo_row = next(row for row in japan_row.location_rows if row.label == "Tokyo")
    tokyo_row.click_toggle_button()
    process_gtk_events()

    widget.filter("Osaka")
    widget.filter("")

    location_state = {
        row.label: (row.get_visible(), row.expanded) for row in japan_row.location_rows
    }
    assert location_state == {"Tokyo": (True, True), "Osaka": (True, False)}
    assert {row.label: row.get_visible() for row in tokyo_row.server_rows} == {"JP#1": True}


def test_filter_matches_secure_core_servers():
    widget = _displayed_widget(server_list=SERVER_LIST_WITH_SECURE_CORE)

    widget.filter("CH-JP#1")

    japan_row = next(row for row in widget.country_rows if row.country_name == "Japan")
    assert japan_row.get_visible()
    assert japan_row.secure_core_row.get_visible()
    assert japan_row.secure_core_row.expanded
    server_visibility = {
        row.label: row.get_visible() for row in japan_row.secure_core_row.server_rows
    }
    assert server_visibility == {"Via Switzerland": True}


def test_filter_hides_secure_core_row_not_matching():
    widget = _displayed_widget(server_list=SERVER_LIST_WITH_SECURE_CORE)

    widget.filter("Osaka")

    japan_row = next(row for row in widget.country_rows if row.country_name == "Japan")
    assert japan_row.get_visible()
    assert not japan_row.secure_core_row.get_visible()


def test_filter_survives_server_list_refresh(unsorted_server_list):
    mock_controller = Mock()
    widget = ServerListWidget(controller=mock_controller)
    widget.display(user_tier=PLUS_TIER, server_list=unsorted_server_list)

    widget.filter("Argentina")
    mock_controller.server_list = unsorted_server_list
    server_list_updated_callback = (
        mock_controller.set_server_list_updated_callback.call_args[0][0]
    )
    server_list_updated_callback()
    process_gtk_events()

    country_visibility = {
        row.country_name: row.get_visible() for row in widget.country_rows
    }
    assert country_visibility == {"Argentina": True, "Japan": False}


def test_server_list_update_is_deferred_while_filter_is_active(
        unsorted_server_list, monkeypatch
):
    """The periodic server list/loads refreshes rebuild the whole widget, so
    they are deferred while a filter is active and applied when it is cleared."""
    monkeypatch.setattr(serverlist_module, "REFRESH_DELAY_MS", 0)
    mock_controller = Mock()
    widget = ServerListWidget(controller=mock_controller)
    widget.display(user_tier=PLUS_TIER, server_list=unsorted_server_list)
    assert len(widget.country_rows) == 2

    widget.filter("Argentina")

    # A server list refresh arrives mid-search, with a different list.
    mock_controller.server_list = SERVER_LIST  # single country
    callback = mock_controller.set_server_list_updated_callback.call_args[0][0]
    callback()
    process_gtk_events()

    # The refresh was deferred: the rows were not rebuilt mid-search.
    assert len(widget.country_rows) == 2

    widget.filter("")
    process_gtk_events()

    # The deferred refresh is applied once the filter is cleared.
    assert len(widget.country_rows) == 1


def _ui_update_counter(widget) -> list:
    """Counts how many times the widget was fully rebuilt (ui-updated)."""
    updates = []
    widget.connect("ui-updated", lambda *_: updates.append(1))
    return updates


def _refresh_callback(mock_controller):
    return mock_controller.set_server_list_updated_callback.call_args[0][0]


def test_server_list_update_never_rebuilds_inline(unsorted_server_list, monkeypatch):
    """A data update handler runs on the UI thread, so a full rebuild there
    would steal the main thread from whatever the user is doing at that
    moment (e.g. typing in the search box). The rebuild runs a moment later,
    off the handler."""
    monkeypatch.setattr(serverlist_module, "REFRESH_DELAY_MS", 0)
    mock_controller = Mock()
    mock_controller.server_list = unsorted_server_list
    widget = ServerListWidget(controller=mock_controller)
    widget.display(user_tier=PLUS_TIER, server_list=unsorted_server_list)
    ui_updates = _ui_update_counter(widget)

    _refresh_callback(mock_controller)()

    assert len(ui_updates) == 0  # no inline rebuild

    process_gtk_events()
    assert len(ui_updates) == 1  # rebuilt off the handler


def test_refresh_landing_in_the_typing_window_stays_deferred(
        unsorted_server_list, monkeypatch
):
    """A refresh landing between a keystroke and the (debounced)
    "search-changed" signal must not rebuild the list mid-search: by the time
    the scheduled rebuild runs, the filter is already active, so the rebuild
    waits until the filter is cleared."""
    monkeypatch.setattr(serverlist_module, "REFRESH_DELAY_MS", 0)
    mock_controller = Mock()
    mock_controller.server_list = unsorted_server_list
    widget = ServerListWidget(controller=mock_controller)
    widget.display(user_tier=PLUS_TIER, server_list=unsorted_server_list)

    # A refresh arrives with a different list, before "search-changed" fires.
    mock_controller.server_list = SERVER_LIST  # single country
    _refresh_callback(mock_controller)()
    widget.filter("Argentina")  # "search-changed" fires before the rebuild runs
    process_gtk_events()

    # Still searching: not rebuilt.
    assert len(widget.country_rows) == 2

    widget.filter("")
    process_gtk_events()

    # Applied once the filter is cleared.
    assert len(widget.country_rows) == 1


def test_clearing_the_filter_does_not_rebuild_inside_the_keystroke_handler(
        unsorted_server_list, monkeypatch
):
    """The rebuild queued while searching runs after filter("") returns, not
    synchronously inside it -- filter("") is called from the search entry's
    "search-changed" handler, and a rebuild there would freeze the UI right
    when the user is typing."""
    monkeypatch.setattr(serverlist_module, "REFRESH_DELAY_MS", 0)
    mock_controller = Mock()
    mock_controller.server_list = unsorted_server_list
    widget = ServerListWidget(controller=mock_controller)
    widget.display(user_tier=PLUS_TIER, server_list=unsorted_server_list)
    ui_updates = _ui_update_counter(widget)

    widget.filter("Argentina")
    _refresh_callback(mock_controller)()  # refresh arrives mid-search -> queued
    widget.filter("")

    assert len(ui_updates) == 0  # no rebuild inside the clear handler

    process_gtk_events()
    assert len(ui_updates) == 1  # rebuilt right after, off the handler


def test_unload_cancels_a_scheduled_rebuild(unsorted_server_list, monkeypatch):
    monkeypatch.setattr(serverlist_module, "REFRESH_DELAY_MS", 0)
    mock_controller = Mock()
    mock_controller.server_list = unsorted_server_list
    widget = ServerListWidget(controller=mock_controller)
    widget.display(user_tier=PLUS_TIER, server_list=unsorted_server_list)
    ui_updates = _ui_update_counter(widget)

    _refresh_callback(mock_controller)()
    widget.unload()
    process_gtk_events()

    assert len(ui_updates) == 0


def test_filter_collapses_country_rows_that_stop_matching():
    """Collapsing hidden rows frees their lazily built children, keeping the
    widget tree small while filtering."""
    widget = _displayed_widget()

    japan_row = widget.country_rows[0]
    japan_row.click_toggle_button()
    process_gtk_events()
    assert japan_row.location_rows

    widget.filter("Nonexistent")

    assert not japan_row.expanded
    assert not japan_row.location_rows
