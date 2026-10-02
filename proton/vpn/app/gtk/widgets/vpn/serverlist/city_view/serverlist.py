"""
This module defines the server list widget.


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
from __future__ import annotations
import time
import locale
from typing import Iterator, List, Optional
import logging
from unittest.mock import Mock

from gi.repository import GLib, GObject

from proton.vpn import logging as proton_logging
from proton.vpn.app.gtk import Gtk
from proton.vpn.app.gtk.controller import Controller
from proton.vpn.app.gtk.translator import LOCALIZATION_ENABLED
from proton.vpn.app.gtk.utils.country import get_localized_country_name
from proton.vpn.app.gtk.utils.safe_signal_connect import safe_signal_connect
from proton.vpn.app.gtk.utils.search import fold
from proton.vpn.session.servers import ServerList, TierEnum
from proton.vpn.session.servers.server_list_fetcher import ServerListFetcher

from proton.vpn.app.gtk.widgets.vpn.serverlist.city_view.country_row import CountryRow
from proton.vpn.app.gtk.widgets.vpn.serverlist.city_view.server_list_header_row import (
    ServerListHeaderRow,
)

from proton.vpn.app.gtk.widgets.vpn.serverlist.city_view.utils import (
    sync_rows_with_model_items,
)

logger = proton_logging.getLogger(__name__)

# How long to wait before rebuilding the widget after a data update. Updates
# can land at any moment (on a slow connection, right in the middle of a
# search), so the rebuild gives way to whatever the user is doing first: if a
# filter is active by the time it runs, it stays deferred until it is cleared.
REFRESH_DELAY_MS = 200

# Maximum time spent filtering (or restoring after a search) country rows
# per main loop iteration, so that a filter pass cannot freeze the UI.
FILTER_CHUNK_DURATION_SECONDS = 0.010


class ServerListWidget(Gtk.ScrolledWindow):
    """Server list widget displaying countries, locations and their servers."""

    def __init__(self, controller: Controller):
        super().__init__()
        self._controller = controller
        self._user_tier: Optional[int] = None

        self.set_policy(
            hscrollbar_policy=Gtk.PolicyType.NEVER,
            vscrollbar_policy=Gtk.PolicyType.AUTOMATIC
        )
        self.set_propagate_natural_width(True)
        self.set_name("server-list-widget")
        self.set_overlay_scrolling(False)

        # pylint: disable=duplicate-code
        self._container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self._container.set_name("server-list-widget-container")
        self._container.set_vexpand(True)
        self._container.set_spacing(5)
        self.set_child(self._container)

        self._header_row = ServerListHeaderRow()
        self._container.prepend(self._header_row)

        self._country_rows_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self._country_rows_container.set_name("country-rows-container")
        self._country_rows_container.set_vexpand(True)
        self._country_rows_container.set_spacing(5)
        self._container.append(self._country_rows_container)

        self._country_rows: List[CountryRow] = []
        self._filter_snapshot: Optional[dict] = None
        self._active_filter: Optional[str] = None
        self._filter_generation = 0
        self._filter_row_iterator: Optional[Iterator[CountryRow]] = None
        self._filter_source_id: Optional[int] = None
        self._pending_refresh = False
        self._pending_refresh_description = ""
        self._refresh_source_id: Optional[int] = None

    def display(self, user_tier: int, server_list: ServerList):
        """Builds and displays the server list."""
        self._user_tier = user_tier
        self._populate_countries(server_list)
        self._controller.set_server_list_updated_callback(self._on_server_list_update)
        self._controller.set_server_loads_updated_callback(self._on_server_loads_update)
        self._controller.set_location_names_updated_callback(self._on_location_names_update)
        if self._active_filter:
            # A server list refresh must not reset the active filter.
            self.filter(self._active_filter)
        self.emit("ui-updated")

    @GObject.Signal(name="ui-updated")
    def ui_updated(self):
        """Signal emitted once the server list within the UI has been updated.
        Mainly used for test purposes."""

    def filter(self, search_text: str):
        """Filters the displayed country rows in place, by the given search text.

        The rows expanded before filtering are restored when the search text
        is cleared.

        The pass is time-sliced: country rows are filtered in chunks on the
        main loop, so a broad query cannot freeze the UI for the whole pass,
        and a new keystroke cancels the pending pass.
        """
        needle = fold(search_text.strip())
        self._filter_generation += 1  # cancels a pass still in flight
        if not needle:
            self._clear_filter()
            return

        if self._filter_snapshot is None:
            self._filter_snapshot = {
                row.country_code.lower(): (row.expanded, self._expanded_groups_of(row))
                for row in self.country_rows
            }

        self._active_filter = needle
        self._filter_row_iterator = iter(self.country_rows)
        self._filter_source_id = GLib.idle_add(
            self._run_filter_chunk, self._filter_generation, needle
        )

    def _run_filter_chunk(self, generation: int, needle: str) -> bool:
        """Filters the next chunk of country rows (runs on the main loop)."""
        if generation != self._filter_generation:
            # A newer keystroke replaced this pass (and its state): just stop.
            return GLib.SOURCE_REMOVE

        deadline = time.monotonic() + FILTER_CHUNK_DURATION_SECONDS
        for row in self._filter_row_iterator:
            row.filter(needle)
            if time.monotonic() >= deadline:
                return GLib.SOURCE_CONTINUE

        self._filter_source_id = None
        self._filter_row_iterator = None
        return GLib.SOURCE_REMOVE

    def _expanded_groups_of(self, row: CountryRow) -> set[str]:
        """Returns the lowercase labels of the row's currently expanded groups."""
        children = row.location_rows + (
            [row.secure_core_row] if row.secure_core_row else []
        )
        return {child.label.lower() for child in children if child.expanded}

    def _clear_filter(self):
        """Clears the filter, making every row visible again and restoring
        the expansion state from before the filter was applied.

        Like the filter pass itself, the restore is time-sliced on the main
        loop: restoring every row inline froze the UI for over a second on
        real server lists. The snapshot is consumed by the last chunk, so a
        new keystroke mid-restore keeps the original pre-filter state."""
        self._active_filter = None
        self._filter_row_iterator = iter(self.country_rows)
        self._filter_source_id = GLib.idle_add(
            self._run_clear_chunk, self._filter_generation, self._filter_snapshot
        )

    def _run_clear_chunk(self, generation: int, snapshot: Optional[dict]) -> bool:
        """Restores the next chunk of country rows (runs on the main loop)."""
        if generation != self._filter_generation:
            # A newer keystroke replaced this pass (and its state): just stop.
            return GLib.SOURCE_REMOVE

        deadline = time.monotonic() + FILTER_CHUNK_DURATION_SECONDS
        for row in self._filter_row_iterator:
            row.set_visible(True)
            if snapshot is not None:
                expanded, expanded_groups = snapshot.get(
                    row.country_code.lower(), (False, set())
                )
                row.restore_expanded_state(
                    expanded=expanded, expanded_groups=expanded_groups
                )
            if time.monotonic() >= deadline:
                return GLib.SOURCE_CONTINUE

        self._filter_source_id = None
        self._filter_row_iterator = None
        self._filter_snapshot = None
        if self._pending_refresh:
            self._schedule_refresh()
        return GLib.SOURCE_REMOVE

    def _populate_countries(self, server_list: ServerList):
        self._display_country_rows(server_list)

    @property
    def country_rows(self) -> List[CountryRow]:
        """Returns the list of country rows currently displayed."""
        return list(self._country_rows)

    def _remove_country_rows(self):
        while self._country_rows:
            row = self._country_rows.pop()
            row.reset()
            self._country_rows_container.remove(row)

    def _display_country_rows(self, server_list: ServerList):
        free_user = self._user_tier == TierEnum.FREE
        countries = server_list.group_by_country(
            group_by_location=True,
            include_free_servers=free_user
        )

        if LOCALIZATION_ENABLED:
            # Sort by the localized name so the order matches what's displayed.
            # Free users get their free countries listed first.
            countries.sort(key=lambda country: (
                0 if (free_user and country.free) else 1,
                locale.strxfrm(get_localized_country_name(country.code)),
            ))
        elif free_user:
            # Free countries first, then by English name.
            countries.sort(key=lambda country: (0 if country.free else 1, country.name))

        # Collect expanded states before refresh (keyed by country code and child group name)
        expanded_countries = {row.country_code.lower(): row.expanded for row in self.country_rows}
        expanded_groups_per_country = {
            country_row.country_code.lower(): set(
                location_row.label.lower() for location_row in (
                    country_row.location_rows
                    + ([country_row.secure_core_row] if country_row.secure_core_row else [])
                )
                if location_row.expanded
            )
            for country_row in self.country_rows
        }

        def display_country_row(row, country):
            expanded = expanded_countries.get(country.code.lower(), False)
            expanded_groups = expanded_groups_per_country.get(country.code.lower())
            row.display(
                self._controller, country, self._user_tier,
                expanded=expanded, expanded_groups=expanded_groups
            )

        sync_rows_with_model_items(
            countries,
            self._country_rows,
            self._country_rows_container,
            CountryRow,
            display_country_row
        )
        self._header_row.set_count(len(countries))

    def _on_server_list_update(self):
        """Whenever a new server list is received the UI should be updated."""
        self._queue_refresh("Full server list widget update")

    def _on_server_loads_update(self):
        """Applies fresh server loads in place, without rebuilding the widget.

        A loads update mutates the server models the rows already reference
        (only Load/Score/Status change; the servers, their grouping and their
        order are unchanged), so the rows just re-read them: collapsed rows
        have nothing to update and rows hidden by an active filter keep their
        visibility. No rebuild, and no "ui-updated".
        """
        start = time.time()
        needs_rebuild = False
        for country_row in self._country_rows:
            needs_rebuild |= country_row.update_server_loads()
        if needs_rebuild:
            # A visible server went in/out of maintenance (or the rows are out
            # of sync with the models): restyling rows in place is not worth
            # it, so fall back to the deferred rebuild.
            self._queue_refresh("Partial server list widget update")
            return
        logger.info(
            f"Server loads applied in place in {time.time() - start:.2f} seconds."
        )

    def _on_location_names_update(self):
        """Whenever refreshed location (city/state) names arrive the UI should be updated."""
        self._queue_refresh("Location names widget update")

    def _queue_refresh(self, description: str):
        """Queues a widget rebuild for the given update type instead of
        running it inline.

        The update handlers run on the UI thread, and a rebuild redraws the
        whole widget, so running one inline would freeze the UI for whatever
        the user is doing at that moment. Data updates can land at any time
        (on a slow connection, right in the middle of a search), so the
        rebuild is postponed briefly: if a filter is active by the time it
        runs, it stays deferred until the filter is cleared.
        """
        self._pending_refresh = True
        self._pending_refresh_description = description
        if self._active_filter:
            logger.info(f"{description} deferred while a filter is active.")
        self._schedule_refresh()

    def _schedule_refresh(self):
        """Schedules the queued rebuild, coalescing bursts of updates (e.g.
        server list followed by loads followed by location names) into a
        single rebuild."""
        if self._refresh_source_id is None:
            self._refresh_source_id = GLib.timeout_add(
                REFRESH_DELAY_MS, self._run_pending_refresh
            )

    def _run_pending_refresh(self) -> bool:
        self._refresh_source_id = None
        if self._active_filter or self._filter_row_iterator is not None \
                or not self._pending_refresh:
            # Still searching (or restoring the rows after a search): stay
            # queued. The last clear chunk schedules the rebuild again once
            # the filter is cleared.
            return GLib.SOURCE_REMOVE
        self._pending_refresh = False
        self._display_server_list(self._pending_refresh_description)
        return GLib.SOURCE_REMOVE

    def _display_server_list(self, description: str):
        start = time.time()
        self.display(self._user_tier, self._controller.server_list)
        logger.info(
            f"{description} completed in {time.time() - start:.2f} seconds."
        )

    def unload(self):
        """Unloads the server list widget and its resources."""
        self._controller.unset_server_list_updated_callback()
        self._controller.unset_server_loads_updated_callback()
        self._controller.unset_location_names_updated_callback()
        self._filter_generation += 1  # cancels a filter/clear pass in flight
        if self._filter_source_id is not None:
            GLib.source_remove(self._filter_source_id)
            self._filter_source_id = None
        self._filter_row_iterator = None
        if self._refresh_source_id is not None:
            GLib.source_remove(self._refresh_source_id)
            self._refresh_source_id = None
        self._pending_refresh = False
        self._remove_country_rows()


def _on_activate(app):
    server_list_widget = ServerListWidget(controller=Mock(spec=Controller))

    win = Gtk.ApplicationWindow(application=app)
    win.set_default_size(400, 600)
    win.set_title("Server List")
    win.get_settings().props.gtk_application_prefer_dark_theme = True
    win.set_child(server_list_widget)
    _load_cached_server_list(server_list_widget)
    GLib.timeout_add_seconds(5, _load_cached_server_list, server_list_widget)
    win.present()


def _load_cached_server_list(server_list_widget: ServerListWidget):
    logger.info("Refreshing server list")
    server_list = ServerListFetcher(session=None).load_from_cache()
    server_list_widget.display(user_tier=2, server_list=server_list)
    return True


def main():
    """Main entry point for testing the server list widget standalone."""
    logger.setLevel(logging.DEBUG)
    app = Gtk.Application()
    safe_signal_connect(app, 'activate', _on_activate)

    app.run(None)


if __name__ == "__main__":
    main()
