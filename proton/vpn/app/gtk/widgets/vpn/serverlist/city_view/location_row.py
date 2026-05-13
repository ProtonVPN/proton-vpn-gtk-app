"""
This module defines the location rows displayed in the server list widget.


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

from gi.repository import GLib

from proton.vpn.session.servers import Location, TierEnum
from proton.vpn.app.gtk import Gtk
from proton.vpn.app.gtk.controller import Controller
from proton.vpn.app.gtk.widgets.vpn.serverlist.city_view.expandable_row import ExpandableRow
from proton.vpn.app.gtk.widgets.vpn.serverlist.city_view.row_content import RowContent
from proton.vpn.app.gtk.widgets.vpn.serverlist.city_view.row_view_model import RowViewModel
from proton.vpn.app.gtk.widgets.vpn.serverlist.city_view.utils import (
    make_connect_callback, sync_rows_with_model_items
)
from proton.vpn.app.gtk.widgets.vpn.serverlist.icons import LocationIcon


class LocationRow(Gtk.Box):
    """Row representing a location in the server list widget."""

    def __init__(self):
        # pylint: disable=duplicate-code
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self._location: Optional[Location] = None
        self._controller = None
        self._user_tier = None
        self._expandable_row = ExpandableRow(
            on_expand=self._add_server_rows,
            on_collapse=self._remove_server_rows,
        )
        self.append(self._expandable_row)
        self._server_rows: List[RowContent] = []

    # pylint: disable=too-many-arguments
    def display(
        self, controller: Controller, location: Location, user_tier: int,
        expanded: bool = False
    ):
        """Displays the location row according to the specified parameters.

        Args:
            controller: The controller instance
            location: The location to display
            user_tier: The user's tier level
            expanded: Whether the location row should be expanded (defaults to False)
        """
        self.reset(keep_server_rows=expanded)
        self._controller = controller
        self._location = location
        self._user_tier = user_tier
        self._expandable_row.connect_toggle()
        upgrade_required = user_tier == TierEnum.FREE and not location.free

        row_data = RowViewModel(
            name=location.name,
            on_connect=make_connect_callback(controller, location.servers, user_tier),
            free=location.free,
            under_maintenance=location.under_maintenance and not upgrade_required,
            features=location.features,
            smart_routing=location.smart_routing,
            toggable=True,
            upgrade_required=upgrade_required,
            icon_factory=LocationIcon,
            connect_button_tooltip=(
                f"Upgrade to connect to {location.name}"
                if upgrade_required else
                f"Connect to {location.name}"
            ),
            toggle_button_tooltips=(
                f"Show all servers from {location.name}",
                f"Hide all servers from {location.name}",
            ),
        )
        self._expandable_row.row_content.display(row_data)
        if expanded:
            self.click_toggle_button()

    def reset(self, keep_server_rows: bool = False):
        """Resets the location row to its initial state."""
        self._expandable_row.reset(keep_children=keep_server_rows)

    @property
    def label(self) -> str:
        """Returns the location label."""
        return self._expandable_row.row_content.label

    @property
    def server_rows(self) -> List[RowContent]:
        """Returns the list of server rows currently displayed."""
        return list(self._server_rows)

    @property
    def expanded(self) -> bool:
        """Returns whether the location row is currently expanded or not."""
        return self._expandable_row.row_content.expanded

    def grab_focus(self):  # pylint: disable=arguments-differ
        """See Gtk.Widget.grab_focus()"""
        self._expandable_row.row_content.grab_focus()

    def click_toggle_button(self):
        """Simulates a click on the toggle button to expand/collapse the row."""
        self._expandable_row.row_content.click_toggle_button()

    def _remove_server_rows(self):
        while self._server_rows:
            server_row = self._server_rows.pop()
            self._expandable_row.remove_child(server_row)
            server_row.reset()

    def _add_server_rows(self):
        servers = self._location.servers
        if self._user_tier == TierEnum.FREE and self._location.free:
            servers = chain(self._location.free_servers, self._location.paid_servers)
        else:
            servers = chain(self._location.paid_servers, self._location.free_servers)

        # Capture controller directly to avoid closing over `self` in on_connect
        controller = self._controller

        # pylint: disable=duplicate-code
        def display_server_row(server_row, server):
            upgrade_required = self._user_tier == TierEnum.FREE and not server.free

            def on_connect():
                future = controller.connect_to_server(server.name)
                future.add_done_callback(lambda f: GLib.idle_add(f.result))

            row_data = RowViewModel(
                name=server.name,
                on_connect=on_connect,
                free=server.free,
                under_maintenance=server.under_maintenance and not upgrade_required,
                features=server.features,
                smart_routing=server.smart_routing,
                toggable=False,
                upgrade_required=upgrade_required,
                load=None if server.under_maintenance else server.load,
                connect_button_tooltip=(
                    f"Upgrade to connect to {server.name}"
                    if upgrade_required else
                    f"Connect to {server.name}"
                ),
            )
            server_row.display(row_data)

        sync_rows_with_model_items(
            list(servers),
            self._server_rows,
            self._expandable_row.container,
            RowContent,
            display_server_row
        )
