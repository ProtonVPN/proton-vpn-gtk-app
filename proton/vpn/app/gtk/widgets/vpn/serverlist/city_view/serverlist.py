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
import itertools
import time
from typing import List
import logging
from unittest.mock import Mock

from gi.repository import GLib, GObject

from proton.vpn import logging as proton_logging
from proton.vpn.app.gtk import Gtk
from proton.vpn.app.gtk.controller import Controller
from proton.vpn.session.servers import ServerList, TierEnum
from proton.vpn.session.servers.server_list_fetcher import ServerListFetcher

from proton.vpn.app.gtk.widgets.vpn.serverlist.city_view.country import CountryRow

logger = proton_logging.getLogger(__name__)


class ServerListWidget(Gtk.ScrolledWindow):
    """Server list widget displaying countries, cities and their servers."""

    def __init__(self, controller: Controller):
        super().__init__()
        self._controller = controller
        self._user_tier = None

        # pylint: disable=duplicate-code
        self._container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self._container.set_name("server-list-widget-container")
        self._container.set_vexpand(True)
        self._container.set_margin_end(10)  # Leave space for the scroll bar.
        self._container.set_spacing(5)
        self.set_child(self._container)

    def display(self, user_tier: int, server_list: ServerList):
        """Builds and displays the server list."""
        self._user_tier = user_tier
        self._populate_countries(server_list)
        self._controller.set_server_list_updated_callback(self._on_server_list_update)
        self._controller.set_server_loads_updated_callback(self._on_server_loads_update)
        self.emit("ui-updated")

    def connection_status_update(self, connection_status):
        """
        This method is called by VPNWidget whenever the VPN connection status changes.
        Important: as this method is always called from another thread, we need
        to make sure that any resulting actions are passed to the main thread
        running GLib's main loop with GLib.idle_add.
        """
        # Not implemented

    def focus_on_entry(self, _widget, name_to_search: str) -> None:
        """Searches for an entry by name and either connects to it directly,
           or focuses on it."""
        # pylint: disable=duplicate-code
        for country in self.country_rows:

            # Server
            if "#" in name_to_search:
                future = self._controller.connect_to_server(name_to_search)
                future.add_done_callback(lambda f: GLib.idle_add(f.result))
                return

            # Country
            if country.country_name.lower() == name_to_search.lower():
                country.grab_focus()
                return

            # City
            for city in country.cities:
                if city.name.lower() == name_to_search.lower():
                    country.focus_on_city(city.name)
                    return

    @GObject.Signal(name="ui-updated")
    def ui_updated(self):
        """Signal emitted once the server list within the UI has been updated.
        Mainly used for test purposes."""

    def _populate_countries(self, server_list: ServerList):
        self._display_country_rows(server_list)

    @property
    def country_rows(self) -> List[CountryRow]:
        """Returns the list of country rows currently displayed."""
        country_rows = []
        country_row = self._container.get_first_child()
        while country_row:
            country_rows.append(country_row)
            country_row = country_row.get_next_sibling()
        return country_rows

    def _remove_country_rows(self):
        for row in self.country_rows:
            row.reset()
            self._container.remove(row)

    def _display_country_rows(self, server_list: ServerList):
        countries = server_list.group_by_country(cities=True)
        if self._user_tier == TierEnum.FREE:
            # If the current user has a free account, sort the countries having
            # free servers first.
            countries.sort(key=lambda country: (0 if country.free else 1, country.name))

        for country, row in itertools.zip_longest(countries, self.country_rows):
            if row is None:
                # More countries than rows
                row = CountryRow()
                self._container.append(row)

            if country is None:
                # More rows than countries
                self._container.remove(row)
            else:
                row.display(self._controller, country, self._user_tier)

    def _on_server_list_update(self):
        """Whenever a new server list is received the UI should be updated."""
        start = time.time()
        self.display(self._user_tier, self._controller.server_list)
        logger.info(
            "Full server list widget update completed in "
            f"{time.time() - start:.2f} seconds."
        )

    def _on_server_loads_update(self):
        start = time.time()
        self.display(self._user_tier, self._controller.server_list)
        logger.info(
            "Partial server list widget update completed in "
            f"{time.time() - start:.2f} seconds."
        )

    def unload(self):
        """Unloads the server list widget and its resources."""
        self._controller.unset_server_list_updated_callback()
        self._controller.unset_server_loads_updated_callback()
        self._remove_country_rows()


def _on_activate(app):
    server_list_widget = ServerListWidget(controller=Mock(spec=Controller))

    win = Gtk.ApplicationWindow(application=app)
    win.set_default_size(400, 600)
    win.set_title("Server List")
    win.get_settings().props.gtk_application_prefer_dark_theme = True
    win.set_child(server_list_widget)
    _load_cached_server_list(server_list_widget)
    GLib.timeout_add_seconds(10, _load_cached_server_list, server_list_widget)
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
    app.connect('activate', _on_activate)

    app.run(None)


if __name__ == "__main__":
    main()
