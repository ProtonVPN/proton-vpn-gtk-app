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

from dataclasses import dataclass, field
from typing import List, Dict

from gi.repository import GLib, GObject

from proton.vpn.app.gtk import Gtk
from proton.vpn.app.gtk.controller import Controller
from proton.vpn.app.gtk.services import VPNDataRefresher
from proton.vpn.app.gtk.widgets.vpn.serverlist.country import CountryRow
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
        new_server_list_handler_id: handler id obtained when connecting
        to the new-server-list signal on VPNDataRefresher.
        new_server_loads_handler_id: handler id obtained when connecting
        to the new-server-loads signal on VPNDataRefresher.
    """
    user_tier: int = None
    server_list: ServerList = None
    country_rows: Dict[str, CountryRow] = field(default_factory=dict)
    new_server_list_handler_id: int = None
    new_server_loads_handler_id: int = None

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
        controller: Controller
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

        self.connect("unrealize", self._on_unrealize)

    def _on_unrealize(self, _widget):
        self.unload()

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

    def _on_server_list_update(
            self, _: VPNDataRefresher, server_list: ServerList
    ):
        """Whenever a new server list is received the UI should be updated."""
        self._state.server_list = server_list
        self._build_country_rows()

    def _on_server_loads_update(
            self,
            _vpn_data_refresher: VPNDataRefresher,
            _server_list: ServerList
    ):
        for country_row in self._state.country_rows.values():
            country_row.update_server_loads()

    def display(self, user_tier: int, server_list: int):
        """Update UI with the new server list."""
        self._state = ServerListWidgetState(
            server_list=server_list,
            user_tier=user_tier
        )

        self._build_country_rows()
        self._state.new_server_list_handler_id = self._controller.vpn_data_refresher.connect(
            "new-server-list", self._on_server_list_update
        )
        self._state.new_server_loads_handler_id = self._controller.vpn_data_refresher.connect(
            "new-server-loads", self._on_server_loads_update
        )

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
        self._controller.vpn_data_refresher.disconnect(
            self._state.new_server_list_handler_id
        )
        self._controller.vpn_data_refresher.disconnect(
            self._state.new_server_loads_handler_id
        )

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
        if self._controller.is_connection_active:
            connected_server_id = self._controller.current_server_id

        new_country_rows = {}
        for country in countries:
            show_country_servers = False
            if old_country_rows and old_country_rows.get(country.code):
                show_country_servers = old_country_rows[country.code].showing_servers

            country_row = CountryRow(
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
    return f"{0 if country.is_free else 1}__{country.name}"
