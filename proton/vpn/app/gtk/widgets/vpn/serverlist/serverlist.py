"""
This module defines the widgets used to present the VPN server list to the user.


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
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import List, Dict

from gi.repository import GLib, GObject

from proton.vpn.app.gtk import Gtk
from proton.vpn.app.gtk.controller import Controller
from proton.vpn.app.gtk.widgets.vpn.serverlist.country import (
    CountryRow, ImmediateCountryRow, DeferredCountryRow)
from proton.vpn.session.servers import Country, LogicalServer, ServerList
from proton.vpn import logging


logger = logging.getLogger(__name__)


@dataclass
class ServerListWidgetState:
    """
    Holds the state of the ServerListWidget. This state is reset after
    login/logout.

    Attributes:
        user_tier: the tier the user has access to.
        server_list: list of servers to be displayed.
        country_rows: country rows indexed by country code.
    """
    user_tier: int = None
    server_list: ServerList = None
    country_rows: Dict[str, CountryRow] = field(default_factory=dict)

    def get_server_by_id(self, server_id: str) -> LogicalServer:
        """Returns the server with the given name."""
        if self.server_list:
            return self.server_list.get_by_id(server_id)
        return None


class ServerListWidget(Gtk.ScrolledWindow):
    """Displays the VPN servers list."""

    # Number of seconds to wait before checking if the servers cache expired.
    RELOAD_INTERVAL_IN_SECONDS = 60

    def __init__(
        self,
        controller: Controller,
        deferred_country_row: bool = False,
    ):
        super().__init__()
        self.set_policy(
            hscrollbar_policy=Gtk.PolicyType.NEVER,
            vscrollbar_policy=Gtk.PolicyType.AUTOMATIC
        )
        self._controller = controller
        self._container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self._container.set_margin_end(15)  # Leave space for the scroll bar.
        self.add(self._container)

        self._state = ServerListWidgetState()
        self._deferred_country_row = deferred_country_row

        self.connect("unrealize", self._on_unrealize)

    def _on_unrealize(self, _widget):
        self.unload()

    @GObject.Signal(name="filter-complete")
    def filter_complete(self):
        """Signal emitted after the UI finalized filtering the UI."""

    @GObject.Signal(name="ui-updated")
    def ui_updated(self):
        """Signal emitted once the server list within the UI has been updated.
        Mainly used for test purposes."""

    @property
    def country_rows(self) -> List[CountryRow]:
        """Returns the list of country rows that are currently being displayed.
        This method was made available for tests."""
        return list(self._state.country_rows.values())

    def connection_status_update(self, connection_status):
        """
        This method is called by VPNWidget whenever the VPN connection status changes.
        Important: as this method is always called from another thread, we need
        to make sure that any resulting actions are passed to the main thread
        running GLib's main loop with GLib.idle_add.
        """
        connection = connection_status.context.connection
        if connection:
            def update_server_rows():
                country_row = self._get_country_row(connection.server_id)
                country_row.connection_status_update(connection_status)

            GLib.idle_add(update_server_rows)

    def _remove_country_rows(self):
        """Remove UI country rows."""
        for row in self._container.get_children():
            self._container.remove(row)
            row.destroy()

    def _on_server_list_update(self):
        """Whenever a new server list is received the UI should be updated."""
        start = time.time()
        self._state.server_list = self._controller.server_list
        self._build_country_rows()
        logger.info(
            "Full server list widget update completed in "
            f"{time.time() - start:.2f} seconds."
        )

    def _on_server_loads_update(self):
        start = time.time()

        new_countries = {
            country.code: country
            for country in self._controller.server_list.group_by_country()
        }

        for country_row in self._state.country_rows.values():
            new_country = new_countries.get(country_row.country_code, None)
            country_row.update_server_loads(new_country)

        logger.info(
            "Partial server list widget update completed in "
            f"{time.time() - start:.2f} seconds."
        )

    def _legacy_filter_ui(self, search_entry: Gtk.SearchEntry):
        """This filters the countries in the server list based on the contents
           of the given search entry.
        """
        start_time = time.time()
        entry_text = search_entry.get_text().lower().replace(" ", "")

        for country_row in self.country_rows:
            country_match = entry_text in country_row.header_searchable_content

            server_match = False
            for server_row in country_row.server_rows:
                # Show server rows if they match the search text, or if they belong to
                # a country that matches the search text. Otherwise, hide them.
                server_row_visible = entry_text in server_row.searchable_content
                server_row.set_visible(server_row_visible or country_match)
                if server_row_visible and entry_text:
                    server_match = True

            # If there was at least a server in the current country row matching
            # the search text then expand country servers. Otherwise, collapse them.
            country_row.set_servers_visibility(server_match)

            # Show the whole country row if there was either a server match or
            # a country match. Otherwise, hide it.
            country_row.set_visible(server_match or country_match)

        self.emit("filter-complete")
        end_time = time.time()
        logger.info(f"Filter done in {(end_time - start_time) * 1000:.2f} ms.")

    def focus_on_entry(self, _widget, name_to_search: str) -> None:
        """Searches for an entry by name and either connects to it directly,
           or focuses on it."""
        for country in self.country_rows:

            # Server
            if "#" in name_to_search:
                future = self._controller.connect_to_server(name_to_search)
                future.add_done_callback(lambda f: GLib.idle_add(f.result))
                return

            # Country
            if country.country_name.lower() == name_to_search.lower():
                if not country.showing_servers:
                    country.toggle_row()
                country.set_can_focus(True)   # required to focus on the expanded country
                country.grab_focus()
                country.set_can_focus(False)  # required to navigate countries with keyboard
                return

    def display(self, user_tier: int, server_list: int):
        """Update UI with the new server list."""
        self._state = ServerListWidgetState(
            server_list=server_list,
            user_tier=user_tier
        )

        self._build_country_rows()
        self._controller.set_server_list_updated_callback(self._on_server_list_update)
        self._controller.set_server_loads_updated_callback(self._on_server_loads_update)

    def _build_country_rows(self):
        self._remove_country_rows()
        self._state.country_rows = self._create_new_country_rows(
            old_country_rows=self._state.country_rows
        )
        self._add_country_rows()
        self._container.show_all()
        self.emit("ui-updated")

    def unload(self):
        """Things to do before the widget is being removed from the window."""
        self._controller.unset_server_list_updated_callback()
        self._controller.unset_server_loads_updated_callback()

    def _add_country_rows(self):
        """Adds country rows to the container."""
        for country_row in self._state.country_rows.values():
            self._container.pack_start(
                country_row,
                expand=False, fill=False, padding=0
            )

    def _create_new_country_rows(self, old_country_rows) -> Dict[str, CountryRow]:
        """Returns new country rows."""
        countries = self._state.server_list.group_by_country()
        if self._state.user_tier == 0:
            # If the current user has a free account, sort the countries having
            # free servers first.
            countries.sort(key=free_countries_first_sorting_key)

        connected_server_id = None
        if self._controller.is_connection_active:  # noqa: E501 # pylint: disable=line-too-long # nosemgrep: python.lang.maintainability.is-function-without-parentheses.is-function-without-parentheses
            connected_server_id = self._controller.current_server_id

        # Chose the deferred loading country row if that was the configuration
        # given to this widget.
        Row = (DeferredCountryRow
               if self._deferred_country_row else ImmediateCountryRow)

        new_country_rows = {}
        for country in countries:
            show_country_servers = False
            if old_country_rows and old_country_rows.get(country.code):
                show_country_servers = old_country_rows[country.code].showing_servers

            country_row = Row(
                country=country,
                user_tier=self._state.user_tier,
                controller=self._controller,
                connected_server_id=connected_server_id,
                show_country_servers=show_country_servers
            )
            new_country_rows[country.code.lower()] = country_row

        return new_country_rows

    def _get_country_row(self, server_id: str) -> CountryRow:
        """Returns a country row based on the vpn server."""
        logical_server = self._state.get_server_by_id(server_id)
        country_code = logical_server.exit_country.lower()
        try:
            return self._state.country_rows[country_code]
        except KeyError as error:
            raise RuntimeError(
                f"Unable to get country row {country_code} for server "
                f"{server_id}."
            ) from error


def free_countries_first_sorting_key(country: Country):
    """
    Returns the comparison key to sort countries according to
    business rules for free users.

    Apart from sorting country rows by country name, free users should
    have countries having free servers sorted first.

    :param country: country row to generate the comparison key for.
    :return: The comparison key.
    """
    return f"{0 if country.is_free else 1}__{country.name}"  # noqa: E501 # pylint: disable=line-too-long # nosemgrep: python.lang.maintainability.is-function-without-parentheses.is-function-without-parentheses
