"""
This module defines the city rows displayed in the server list widget.


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

from itertools import chain
from typing import List, Optional, Tuple

from proton.vpn import logging
from proton.vpn.session.servers import City, TierEnum
from proton.vpn.app.gtk import Gtk
from proton.vpn.app.gtk.controller import Controller
from proton.vpn.app.gtk.widgets.vpn.serverlist.city_view.header import ServerLocationHeader
from proton.vpn.app.gtk.widgets.vpn.serverlist.icons import CityIcon


logger = logging.getLogger(__name__)


class CityRow(Gtk.Box):
    """Row representing a city in the server list widget."""

    def __init__(self):  # pylint: disable=duplicate-code
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self._city: Optional[City] = None
        self._header = ServerLocationHeader()
        self.append(self._header)
        self._children_revealer = Gtk.Revealer()
        self._children_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self._children_container.set_spacing(5)
        self._children_container.set_margin_top(5)
        self._children_revealer.set_child(self._children_container)
        self.append(self._children_revealer)
        self._controller = None
        self._user_tier = None
        self._connected_signals: List[Tuple[int, Gtk.Widget]] = []

    def display(
        self, controller: Controller, city: City, user_tier: int,
        connected_server_id: str = None
    ):
        """Displays the city row according to the specified parameters."""
        self.reset()
        self._controller = controller
        self._city = city
        self._user_tier = user_tier
        self._header.connect(
            "toggle-children", self._on_toggle_children
        )
        self._header.display(
            controller, city, user_tier,
            CityIcon(), connected_server_id
        )

    def reset(self):
        """Resets the city row to its initial state."""
        for signal_id, widget in self._connected_signals:
            widget.disconnect(signal_id)
        self._connected_signals.clear()

        self._header.reset()
        self._remove_server_rows()

    @property
    def label(self) -> str:
        """Returns the city label."""
        return self._header.label

    @property
    def server_rows(self) -> List[ServerLocationHeader]:
        """Returns the list of server rows currently displayed."""
        server_rows = []
        server_row = self._children_container.get_first_child()
        while server_row:
            server_rows.append(server_row)
            server_row = server_row.get_next_sibling()
        return server_rows

    def grab_focus(self):  # pylint: disable=arguments-differ
        """See Gtk.Widget.grab_focus()"""
        self._header.grab_focus()

    def click_toggle_button(self):
        """Simulates a click on the toggle button to expand/collapse the row."""
        self._header.click_toggle_button()

    def _on_toggle_children(self, header: ServerLocationHeader):
        self._remove_server_rows()
        if header.expanded:
            self._add_server_rows()
        self._children_revealer.set_reveal_child(
            header.expanded
        )

    def _remove_server_rows(self):
        for server_row in self.server_rows:
            self._children_container.remove(server_row)
            server_row.reset()

    def _add_server_rows(self):
        servers = self._city.servers
        if self._user_tier == TierEnum.FREE and self._city.free:
            # If the current user has a free account, display first the free servers
            servers = chain(self._city.free_servers, self._city.paid_servers)

        for server in servers:
            server_row = ServerLocationHeader()
            server_row.display(self._controller, server, self._user_tier)
            self._children_container.append(server_row)
