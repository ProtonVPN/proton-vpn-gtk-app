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
from gi.repository import GLib
from proton.vpn.session.servers import ServerList
from proton.vpn.session.servers.types import ServerLoad

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


SERVER_LIST_WITH_MANY_SERVERS = ServerList.from_dict({
    "LogicalServers": [
        {
            "ID": i,
            "Name": f"JP#{i}",
            "Status": 1,
            "Load": 50,
            "Servers": [{"Status": 1}],
            "ExitCountry": "JP",
            "City": "Tokyo",
            "Tier": PLUS_TIER,
        }
        for i in range(1, 16)  # 15 servers: more than the auto-expand cap
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


@pytest.fixture
def two_server_list():
    """A fresh ServerList (AR#1 and AR#2, load 50) that tests may mutate."""
    return ServerList.from_dict({
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
    process_gtk_events()

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
    process_gtk_events()

    assert japan_row.get_visible()
    assert not japan_row.expanded
    assert not japan_row.location_rows


def test_filter_expands_country_matched_via_child():
    widget = _displayed_widget()

    japan_row = widget.country_rows[0]
    widget.filter("Tokyo")
    process_gtk_events()

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
    process_gtk_events()

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
    process_gtk_events()

    location_visibility = {
        row.label: row.get_visible() for row in japan_row.location_rows
    }
    assert location_visibility == {"Tokyo": True, "Osaka": False}


def test_filter_shows_location_matching_server_name():
    widget = _displayed_widget()

    japan_row = widget.country_rows[0]
    widget.filter("JP#2")
    process_gtk_events()

    location_visibility = {
        row.label: (row.get_visible(), row.expanded) for row in japan_row.location_rows
    }
    assert location_visibility == {"Tokyo": (False, False), "Osaka": (True, True)}

    osaka_row = next(row for row in japan_row.location_rows if row.label == "Osaka")
    server_visibility = {
        row.label: row.get_visible() for row in osaka_row.server_rows
    }
    assert server_visibility == {"JP#2": True}


def test_filter_does_not_auto_expand_locations_with_many_matching_servers():
    """Auto-expanding a location builds every one of its server row widgets
    (~1ms each): typing "us" auto-expanded all US locations and built ~5800
    row widgets, freezing the UI for ~5.5 seconds per keystroke. Locations
    matching through a broad query stay collapsed (and can be expanded
    manually); only focused matches are auto-expanded."""
    widget = _displayed_widget(server_list=SERVER_LIST_WITH_MANY_SERVERS)

    widget.filter("jp")  # matches every server name in the location
    process_gtk_events()

    japan_row = widget.country_rows[0]
    tokyo_row = japan_row.location_rows[0]
    assert tokyo_row.get_visible()   # the matching location is shown...
    assert not tokyo_row.expanded    # ...but not auto-expanded


def test_clearing_filter_restores_previous_state():
    widget = _displayed_widget()

    japan_row = widget.country_rows[0]
    japan_row.click_toggle_button()
    process_gtk_events()
    tokyo_row = next(row for row in japan_row.location_rows if row.label == "Tokyo")
    tokyo_row.click_toggle_button()
    process_gtk_events()

    widget.filter("Osaka")
    process_gtk_events()
    widget.filter("")
    process_gtk_events()

    location_state = {
        row.label: (row.get_visible(), row.expanded) for row in japan_row.location_rows
    }
    assert location_state == {"Tokyo": (True, True), "Osaka": (True, False)}
    assert {row.label: row.get_visible() for row in tokyo_row.server_rows} == {"JP#1": True}


def test_filter_matches_secure_core_servers():
    widget = _displayed_widget(server_list=SERVER_LIST_WITH_SECURE_CORE)

    widget.filter("CH-JP#1")
    process_gtk_events()

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
    process_gtk_events()

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


def _loads_callback(mock_controller):
    return mock_controller.set_server_loads_updated_callback.call_args[0][0]


def _expanded_server_rows(widget):
    """Expands the only country row and its only location row, and returns
    the location row together with its built server rows indexed by label."""
    country_row = widget.country_rows[0]
    country_row.click_toggle_button()
    process_gtk_events()
    location_row = country_row.location_rows[0]
    location_row.click_toggle_button()
    process_gtk_events()
    return location_row, {row.label: row for row in location_row.server_rows}


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


def test_filter_pass_yields_to_the_main_loop(unsorted_server_list, monkeypatch):
    """A filter pass runs in time-sliced chunks: a callback queued after the
    pass starts runs before the pass reaches the last row. A pass that filters
    every row inline would freeze the UI for its whole duration (measured at
    6 seconds for broad queries like "us")."""
    monkeypatch.setattr(serverlist_module, "FILTER_CHUNK_DURATION_SECONDS", 0)
    widget = _displayed_widget(server_list=unsorted_server_list)

    last_row = widget.country_rows[-1]
    marker_ran = False
    last_row_visible_at_marker = None

    def marker():
        nonlocal marker_ran, last_row_visible_at_marker
        marker_ran = True
        last_row_visible_at_marker = last_row.get_visible()
        return GLib.SOURCE_REMOVE

    widget.filter("Argentina")
    GLib.idle_add(marker)
    process_gtk_events()

    assert marker_ran
    assert last_row_visible_at_marker  # filtered in a later chunk
    assert not last_row.get_visible()  # ...but filtered by the end


def test_new_keystroke_cancels_the_pending_filter_pass(
        unsorted_server_list, monkeypatch
):
    """A keystroke while a filter pass is still running cancels the stale
    pass: only the newest needle is applied."""
    monkeypatch.setattr(serverlist_module, "FILTER_CHUNK_DURATION_SECONDS", 0)
    widget = _displayed_widget(server_list=unsorted_server_list)

    widget.filter("Argentina")  # its pass only starts...
    widget.filter("Japan")      # ...this keystroke cancels it mid-flight

    process_gtk_events()

    country_visibility = {
        row.country_name: row.get_visible() for row in widget.country_rows
    }
    assert country_visibility == {"Argentina": False, "Japan": True}


def test_clearing_the_filter_also_yields_to_the_main_loop(
        unsorted_server_list, monkeypatch
):
    """Restoring every row after clearing the search is chunked too
    (clearing "us" was measured at 1.4 seconds of frozen UI)."""
    monkeypatch.setattr(serverlist_module, "FILTER_CHUNK_DURATION_SECONDS", 0)
    widget = _displayed_widget(server_list=unsorted_server_list)

    widget.filter("Argentina")
    process_gtk_events()
    japan_row = widget.country_rows[-1]

    marker_ran = False
    japan_visible_at_marker = None

    def marker():
        nonlocal marker_ran, japan_visible_at_marker
        marker_ran = True
        japan_visible_at_marker = japan_row.get_visible()
        return GLib.SOURCE_REMOVE

    widget.filter("")
    GLib.idle_add(marker)
    process_gtk_events()

    assert marker_ran
    assert not japan_visible_at_marker  # restored in a later chunk
    assert japan_row.get_visible()      # ...but restored by the end


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
    process_gtk_events()

    assert not japan_row.expanded
    assert not japan_row.location_rows


def test_server_loads_update_updates_displayed_loads_in_place(
        two_server_list, monkeypatch
):
    """A loads update mutates the server models the rows already reference,
    so the displayed loads can be applied inline, without rebuilding."""
    monkeypatch.setattr(serverlist_module, "REFRESH_DELAY_MS", 0)
    mock_controller = Mock()
    mock_controller.server_list = two_server_list
    widget = ServerListWidget(controller=mock_controller)
    widget.display(user_tier=PLUS_TIER, server_list=two_server_list)
    ui_updates = _ui_update_counter(widget)
    location_row, rows_by_label = _expanded_server_rows(widget)
    assert rows_by_label["AR#1"].server_load == "50%"
    assert rows_by_label["AR#2"].server_load == "50%"
    row_ids_before = [id(row) for row in location_row.server_rows]

    two_server_list.update([
        ServerLoad({"ID": 1, "Load": 25, "Score": 1, "Status": 1}),
        ServerLoad({"ID": 2, "Load": 75, "Score": 2, "Status": 1}),
    ])
    _loads_callback(mock_controller)()

    # Applied inline: no process_gtk_events() in between.
    assert rows_by_label["AR#1"].server_load == "25%"
    assert rows_by_label["AR#2"].server_load == "75%"
    assert [id(row) for row in location_row.server_rows] == row_ids_before
    assert len(ui_updates) == 0


def test_server_loads_update_does_not_create_or_destroy_rows(two_server_list):
    mock_controller = Mock()
    mock_controller.server_list = two_server_list
    widget = ServerListWidget(controller=mock_controller)
    widget.display(user_tier=PLUS_TIER, server_list=two_server_list)
    ui_updates = _ui_update_counter(widget)
    country_row = widget.country_rows[0]
    location_row, _ = _expanded_server_rows(widget)

    state_before = (
        [id(row) for row in widget.country_rows],
        len(country_row.location_rows),
        [id(row) for row in location_row.server_rows],
        country_row.expanded,
        location_row.expanded,
    )

    two_server_list.update([
        ServerLoad({"ID": 1, "Load": 25, "Score": 1, "Status": 1}),
        ServerLoad({"ID": 2, "Load": 75, "Score": 2, "Status": 1}),
    ])
    _loads_callback(mock_controller)()
    process_gtk_events()

    state_after = (
        [id(row) for row in widget.country_rows],
        len(country_row.location_rows),
        [id(row) for row in location_row.server_rows],
        country_row.expanded,
        location_row.expanded,
    )
    assert state_after == state_before
    assert len(ui_updates) == 0


def test_server_loads_update_is_not_deferred_while_filter_is_active(two_server_list):
    """Loads used to stay stale on screen until a search filter was cleared
    (the rebuild the loads update queued stayed deferred). They are now
    applied inline, without touching the filter state."""
    mock_controller = Mock()
    mock_controller.server_list = two_server_list
    widget = ServerListWidget(controller=mock_controller)
    widget.display(user_tier=PLUS_TIER, server_list=two_server_list)
    ui_updates = _ui_update_counter(widget)
    _, rows_by_label = _expanded_server_rows(widget)

    widget.filter("AR#1")
    process_gtk_events()
    visibility_before = {
        label: row.get_visible() for label, row in rows_by_label.items()
    }
    assert visibility_before == {"AR#1": True, "AR#2": False}

    two_server_list.update([
        ServerLoad({"ID": 1, "Load": 25, "Score": 1, "Status": 1}),
        ServerLoad({"ID": 2, "Load": 75, "Score": 2, "Status": 1}),
    ])
    _loads_callback(mock_controller)()

    assert rows_by_label["AR#1"].server_load == "25%"  # applied right away
    visibility_after = {
        label: row.get_visible() for label, row in rows_by_label.items()
    }
    assert visibility_after == visibility_before
    process_gtk_events()
    assert len(ui_updates) == 0


def test_server_loads_update_keeps_visibility_and_expansion_untouched(two_server_list):
    mock_controller = Mock()
    mock_controller.server_list = two_server_list
    widget = ServerListWidget(controller=mock_controller)
    widget.display(user_tier=PLUS_TIER, server_list=two_server_list)
    ui_updates = _ui_update_counter(widget)
    country_row = widget.country_rows[0]
    location_row, rows_by_label = _expanded_server_rows(widget)
    widget.filter("AR#1")
    process_gtk_events()

    state_before = (
        country_row.get_visible(), country_row.expanded,
        location_row.get_visible(), location_row.expanded,
        {label: row.get_visible() for label, row in rows_by_label.items()},
        len(location_row.server_rows),  # built children are retained
    )

    two_server_list.update([
        ServerLoad({"ID": 1, "Load": 25, "Score": 1, "Status": 1}),
        ServerLoad({"ID": 2, "Load": 75, "Score": 2, "Status": 1}),
    ])
    _loads_callback(mock_controller)()
    process_gtk_events()

    state_after = (
        country_row.get_visible(), country_row.expanded,
        location_row.get_visible(), location_row.expanded,
        {label: row.get_visible() for label, row in rows_by_label.items()},
        len(location_row.server_rows),
    )
    assert state_after == state_before
    assert len(ui_updates) == 0


def test_server_loads_update_falls_back_to_rebuild_when_maintenance_changes(
        two_server_list, monkeypatch
):
    """Restyling a row (swapping the connect button for the maintenance icon)
    is not done in place: the loads update falls back to the usual deferred
    rebuild."""
    monkeypatch.setattr(serverlist_module, "REFRESH_DELAY_MS", 0)
    mock_controller = Mock()
    mock_controller.server_list = two_server_list
    widget = ServerListWidget(controller=mock_controller)
    widget.display(user_tier=PLUS_TIER, server_list=two_server_list)
    ui_updates = _ui_update_counter(widget)
    _expanded_server_rows(widget)

    # AR#2 goes under maintenance.
    two_server_list.update([ServerLoad({"ID": 2, "Load": 75, "Score": 2, "Status": 0})])
    _loads_callback(mock_controller)()
    process_gtk_events()

    assert len(ui_updates) == 1  # the deferred rebuild ran
    location_row = widget.country_rows[0].location_rows[0]
    rows_by_label = {row.label: row for row in location_row.server_rows}
    assert rows_by_label["AR#2"].under_maintenance_icon.get_visible()


def test_server_loads_update_with_no_displayed_rows_is_a_no_op(monkeypatch):
    monkeypatch.setattr(serverlist_module, "REFRESH_DELAY_MS", 0)
    empty_server_list = ServerList.from_dict({
        "LogicalServers": [],
        "MaxTier": PLUS_TIER
    })
    mock_controller = Mock()
    mock_controller.server_list = empty_server_list
    widget = ServerListWidget(controller=mock_controller)
    widget.display(user_tier=PLUS_TIER, server_list=empty_server_list)
    ui_updates = _ui_update_counter(widget)

    _loads_callback(mock_controller)()
    process_gtk_events()

    assert not widget.country_rows
    assert len(ui_updates) == 0
