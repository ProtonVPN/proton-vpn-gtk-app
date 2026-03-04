"""
Toggleable "Via Secure Core" row for the country, listing secure core servers.

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

from typing import List, Optional

from proton.vpn.app.gtk import Gtk
from proton.vpn.app.gtk.controller import Controller
from proton.vpn.session.dataclasses.servers import SecureCoreGroup
from proton.vpn.session.servers import LogicalServer

from proton.vpn.app.gtk.widgets.vpn.serverlist.city_view.expandable_row import ExpandableRow
from proton.vpn.app.gtk.widgets.vpn.serverlist.city_view.row_content import RowContent
from proton.vpn.app.gtk.widgets.vpn.serverlist.city_view.utils import sync_rows_with_model_items
from proton.vpn.app.gtk.widgets.vpn.serverlist.icons import (
    DoubleFlagIcon,
    SecureCoreIcon,
)


class SecureCoreRow(Gtk.Box):
    """Toggleable row with label "Via Secure Core" that expands to show secure core servers."""
    LABEL = "Via Secure Core"

    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self._secure_core_group: Optional[SecureCoreGroup] = None
        self._controller: Optional[Controller] = None
        self._user_tier: Optional[int] = None
        self._expandable_row = ExpandableRow(
            on_expand=self._add_server_rows,
            on_collapse=self._remove_server_rows,
        )
        self.append(self._expandable_row)

    # pylint: disable=too-many-arguments
    def display(
        self,
        controller: Controller,
        secure_core_group: SecureCoreGroup,
        user_tier: int,
        connected_server_id: Optional[str] = None,
        expanded: bool = False,
    ) -> None:
        """Displays the secure core row according to the specified parameters."""
        self._controller = controller
        self._secure_core_group = secure_core_group
        self._user_tier = user_tier
        self._expandable_row.reset(keep_children=False)
        self._expandable_row.connect_toggle()
        exit_country_name = secure_core_group.servers[0].exit_country_name
        connect_button_tooltip = f"Connect to {exit_country_name} via Secure Core"
        toggle_button_tooltips = (
            f"Show all Secure Core servers\nto connect to {exit_country_name}",
            f"Hide all Secure Core servers\nto connect to {exit_country_name}"
        )
        self._expandable_row.row_content.display(
            controller, secure_core_group, user_tier,
            SecureCoreIcon(), connected_server_id,
            label=self.LABEL,
            show_feature_icons=False,
            connect_button_tooltip=connect_button_tooltip,
            toggle_button_tooltips=toggle_button_tooltips
        )
        if expanded:
            self._expandable_row.row_content.click_toggle_button()

    @property
    def server_rows(self) -> List[RowContent]:
        """Returns the list of server rows currently displayed."""
        return self._expandable_row.get_children()

    @property
    def expanded(self) -> bool:
        """Returns whether the secure core row is currently expanded or not."""
        return self._expandable_row.row_content.expanded

    @property
    def label(self) -> str:
        """Returns the label of the secure core row."""
        return self._expandable_row.row_content.label

    def reset(self, keep_children: bool = False) -> None:
        """Resets the secure core row to its initial state."""
        self._expandable_row.reset(keep_children=keep_children)

    def _remove_server_rows(self) -> None:
        for server_row in self._expandable_row.get_children():
            self._expandable_row.remove_child(server_row)
            server_row.reset()

    def _add_server_rows(self) -> None:
        def display_server_row(server_row: RowContent, server: LogicalServer) -> None:
            label = f"Via {server.entry_country_name}"
            connect_button_tooltip = (
                f"Connect to {server.exit_country_name}\nvia {server.entry_country_name}"
            )
            server_row.display(
                self._controller,
                server,
                self._user_tier,
                icon=DoubleFlagIcon(
                    exit_country_code=server.exit_country,
                    entry_country_code=server.entry_country,
                ),
                label=label,
                show_feature_icons=False,
                connect_button_tooltip=connect_button_tooltip
            )

        sync_rows_with_model_items(
            list(self._secure_core_group.servers),
            self.server_rows,
            self._expandable_row.container,
            RowContent,
            display_server_row,
        )
