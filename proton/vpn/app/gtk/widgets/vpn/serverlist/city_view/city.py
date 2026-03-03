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
from typing import List, Optional

from proton.vpn.session.servers import City, TierEnum
from proton.vpn.app.gtk import Gtk
from proton.vpn.app.gtk.controller import Controller
from proton.vpn.app.gtk.widgets.vpn.serverlist.city_view.expandable_row import ExpandableRow
from proton.vpn.app.gtk.widgets.vpn.serverlist.city_view.row_content import RowContent
from proton.vpn.app.gtk.widgets.vpn.serverlist.city_view.utils import sync_rows_with_model_items
from proton.vpn.app.gtk.widgets.vpn.serverlist.icons import CityIcon


class CityRow(Gtk.Box):
    """Row representing a city in the server list widget."""

    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self._city: Optional[City] = None
        self._controller = None
        self._user_tier = None
        self._expandable_row = ExpandableRow(
            on_expand=self._add_server_rows,
            on_collapse=self._remove_server_rows,
        )
        self.append(self._expandable_row)

    # pylint: disable=too-many-arguments
    def display(
        self, controller: Controller, city: City, user_tier: int,
        connected_server_id: str = None, expanded: bool = False
    ):
        """Displays the city row according to the specified parameters.

        Args:
            controller: The controller instance
            city: The city to display
            user_tier: The user's tier level
            connected_server_id: Optional connected server ID
            expanded: Whether the city should be expanded (defaults to False)
        """
        self.reset(keep_server_rows=expanded)
        self._controller = controller
        self._city = city
        self._user_tier = user_tier
        self._expandable_row.connect_toggle()
        self._expandable_row.row_content.display(
            controller, city, user_tier,
            CityIcon(), connected_server_id
        )
        if expanded:
            self.click_toggle_button()

    def reset(self, keep_server_rows: bool = False):
        """Resets the city row to its initial state."""
        self._expandable_row.reset(keep_children=keep_server_rows)

    @property
    def label(self) -> str:
        """Returns the city label."""
        return self._expandable_row.row_content.label

    @property
    def server_rows(self) -> List[RowContent]:
        """Returns the list of server rows currently displayed."""
        return self._expandable_row.get_children()

    @property
    def expanded(self) -> bool:
        """Returns whether the city row is currently expanded or not."""
        return self._expandable_row.row_content.expanded

    def grab_focus(self):  # pylint: disable=arguments-differ
        """See Gtk.Widget.grab_focus()"""
        self._expandable_row.row_content.grab_focus()

    def click_toggle_button(self):
        """Simulates a click on the toggle button to expand/collapse the row."""
        self._expandable_row.row_content.click_toggle_button()

    def _remove_server_rows(self):
        for server_row in self._expandable_row.get_children():
            self._expandable_row.remove_child(server_row)
            server_row.reset()

    def _add_server_rows(self):
        servers = self._city.servers
        if self._user_tier == TierEnum.FREE and self._city.free:
            servers = chain(self._city.free_servers, self._city.paid_servers)

        def display_server_row(server_row, server):
            server_row.display(self._controller, server, self._user_tier)

        sync_rows_with_model_items(
            list(servers),
            self.server_rows,
            self._expandable_row.container,
            RowContent,
            display_server_row
        )
