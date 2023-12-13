"""
This module defines the server widget.


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
from typing import List, Optional

from gi.repository import GLib, Pango, Atk

from proton.vpn.app.gtk.utils import accessibility
from proton.vpn.app.gtk.utils.search import normalize
from proton.vpn.connection.enum import ConnectionStateEnum
from proton.vpn.session.servers import LogicalServer, ServerFeatureEnum
from proton.vpn.app.gtk.widgets.vpn.serverlist.icons import \
    UnderMaintenanceIcon, SmartRoutingIcon, StreamingIcon, \
    P2PIcon, TORIcon, SecureCoreIcon
from proton.vpn.app.gtk import Gtk
from proton.vpn import logging

from proton.vpn.app.gtk.controller import Controller

logger = logging.getLogger(__name__)


# pylint: disable=too-many-instance-attributes
class ServerRow(Gtk.Box):
    """Displays a single server as a row in the server list."""
    def __init__(self, server: LogicalServer, user_tier: int, controller: Controller):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL)
        self._server = server
        self._user_tier = user_tier
        self._controller = controller
        self._connection_state: ConnectionStateEnum = None
        self._server_details: Optional[Gtk.Box] = None
        self._icons_displayed = []
        self._under_maintenance_icon: Optional[UnderMaintenanceIcon] = None
        self._server_load: Optional[ServerLoad] = None
        self._connect_button: Optional[Gtk.Button] = None

        self._build_row()

    @property
    def connection_state(self):
        """Returns the connection state of the server shown in this row."""
        return self._connection_state

    @connection_state.setter
    def connection_state(self, connection_state: ConnectionStateEnum):
        """Sets the connection state, modifying the row depending on the state."""
        self._connection_state = connection_state

        if (
            self._connection_state == ConnectionStateEnum.CONNECTED
            and not self.available
        ):
            logger.warning(
                "Received connected state but server is not available",
                category="ui", event="conn:state"
            )

        if self.available:
            # Update the server row according to the connection state.
            method = f"_on_connection_state_{connection_state.name.lower()}"
            if hasattr(self, method):
                getattr(self, method)()

    def _build_row(self):
        self._server_label = Gtk.Label(label=self._server.name)
        # Some test server names are very long.
        self._server_label.set_ellipsize(Pango.EllipsizeMode.END)
        self.pack_start(
            self._server_label,
            expand=False, fill=False, padding=10
        )

        self._show_under_maintenance_icon_or_server_details(self._server.enabled)

    def _show_under_maintenance_icon_or_server_details(self, server_enabled: bool):
        if server_enabled:
            self._show_server_details()
        else:
            self._show_under_maintenance_icon()

    def _show_under_maintenance_icon(self):
        if self._server_details:
            self._server_details.hide()

        if not self._under_maintenance_icon:
            self._under_maintenance_icon = UnderMaintenanceIcon(self._server.name)
            self.pack_end(
                self._under_maintenance_icon,
                expand=False, fill=False, padding=10
            )

        self._under_maintenance_icon.show()
        self._server_label.set_property("sensitive", False)

    def _show_server_details(self):
        if self._under_maintenance_icon:
            self._under_maintenance_icon.hide()

        if not self._server_details:
            self._server_details = self._build_server_details()
            self.pack_end(self._server_details, expand=False, fill=False, padding=0)

        self._server_details.show()
        self._server_label.set_property("sensitive", True)

    def _build_server_details(self) -> Gtk.Box:
        server_details = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        if self.upgrade_required:
            button = self._build_upgrade_link_button()
            server_details.pack_end(button, expand=False, fill=False, padding=10)
        else:
            self._connect_button = self._build_connect_button()
            button = self._connect_button
            server_details.pack_end(self._connect_button, expand=False, fill=False, padding=10)

        button_relationships = [(self._server_label, Atk.RelationType.LABELLED_BY)]

        self._server_load = ServerLoad(self._server.load)
        button_relationships.append((self._server_load, Atk.RelationType.DESCRIBED_BY))
        server_details.pack_end(self._server_load, expand=False, fill=False, padding=10)

        server_row_icons = []

        # If server supports Secure Core then it should be the only
        # icon to be displayed.
        if ServerFeatureEnum.SECURE_CORE in self._server.features:
            server_row_icons.append(
                SecureCoreIcon(self._server.entry_country_name, self._server.exit_country_name)
            )
        else:
            smart_routing = self._server.host_country is not None
            if smart_routing:
                server_row_icons.append(SmartRoutingIcon())

            server_feature_icons = self._build_server_feature_icons()
            server_row_icons.extend(server_feature_icons)

        for icon in server_row_icons:
            button_relationships.append((icon, Atk.RelationType.DESCRIBED_BY))
            server_details.pack_end(icon, expand=False, fill=False, padding=0)
            self._icons_displayed.append(icon)

        accessibility.add_widget_relationships(button, button_relationships)

        return server_details

    def _build_connect_button(self):
        connect_button = Gtk.Button(label="Connect")
        connect_button.connect("clicked", self._on_connect_button_clicked)
        connect_button.get_style_context().add_class("secondary")
        return connect_button

    def _build_upgrade_link_button(self):
        upgrade_button = Gtk.LinkButton.new_with_label("Upgrade")
        upgrade_button.set_uri("https://account.protonvpn.com/")
        return upgrade_button

    def _build_server_feature_icons(self) -> List[Gtk.Image]:
        server_feature_icons = []

        if self._server.tier > 0:
            server_feature_icons.append(StreamingIcon())
        if ServerFeatureEnum.P2P in self._server.features:
            server_feature_icons.append(P2PIcon())
        if ServerFeatureEnum.TOR in self._server.features:
            server_feature_icons.append(TORIcon())

        return server_feature_icons

    def _on_connection_state_disconnected(self):
        """Flags this server as "not connected"."""
        self._connect_button.set_sensitive(True)
        self._connect_button.set_tooltip_text(f"Connect to {self.server_label}")
        self._connect_button.set_label("Connect")

    def _on_connection_state_connecting(self):
        """Flags this server as "connecting"."""
        self._connect_button.set_label("Connecting...")
        self._connect_button.set_tooltip_text(f"Connecting to {self.server_label}...")
        self._connect_button.set_sensitive(False)

    def _on_connection_state_connected(self):
        """Flags this server as "connected"."""
        self._connect_button.set_sensitive(False)
        self._connect_button.set_tooltip_text(f"Connected to {self.server_label}")
        self._connect_button.set_label("Connected")

    def _on_connection_state_disconnecting(self):
        pass

    def _on_connection_state_error(self):
        """Flags this server as "not connected"."""
        self._on_connection_state_disconnected()

    def _on_connect_button_clicked(self, _):
        future = self._controller.connect_to_server(self._server.name)
        future.add_done_callback(lambda f: GLib.idle_add(f.result))  # bubble up exceptions if any.

    @property
    def available(self) -> bool:
        """Returns True if the country is available, meaning the user can
        connect to one of its servers. Otherwise, it returns False."""
        return not self.upgrade_required and not self.under_maintenance

    @property
    def upgrade_required(self) -> bool:
        """Returns if a plan upgrade is required to connect to server."""
        return self._server.tier > self._user_tier

    @property
    def server_label(self) -> str:
        """Returns the server label."""
        return self._server_label.get_label()

    @property
    def server_id(self) -> str:
        """Returns the server ID."""
        return self._server.id

    @property
    def server_tier(self) -> int:
        """Returns the server tier."""
        return self._server.tier

    @property
    def under_maintenance(self) -> bool:
        """Returns if the server is under maintenance."""
        return not self._server.enabled

    @property
    def searchable_content(self) -> str:
        """Returns searchable content on this server."""
        return normalize(self.server_label)

    def click_connect_button(self):
        """Clicks the connect button.
        This method was made available for tests."""
        self._connect_button.clicked()

    @property
    def is_connect_button_visible(self) -> bool:
        """Returns if the connect button is visible.
        This method was made available for tests."""
        return self._connect_button.is_visible()

    @property
    def server_load_label(self) -> str:
        """Returns the text shown as server load."""
        return self._server_load.get_text()

    @property
    def under_maintenance_icon_visible(self) -> bool:
        """Whether the under maintenance icon is shown or not."""
        return self._under_maintenance_icon and self._under_maintenance_icon.is_visible()

    def is_server_feature_icon_displayed(self, icon_class):
        """Returns True if an instance of the specified icon class is displayed
        or False otherwise."""
        if not self._server_details.is_visible():
            return False

        filtered_icons = [
            child for child in self._server_details.get_children()
            if isinstance(child, icon_class)
        ]

        return bool(filtered_icons)

    def update_server_load(self):
        """Redraws the row after a server load update."""
        # The server status may have changed
        self._show_under_maintenance_icon_or_server_details(self._server.enabled)
        if self._server.enabled:
            self._server_load.set_load(self._server.load)


class ServerLoad(Gtk.Label):
    """Displays the server load shown in a server row."""
    def __init__(self, load: int):
        super().__init__()
        self.set_name("server-load")

        self.set_load(load)

    def set_load(self, load: int):
        """Sets the load percentage to be displayed."""
        self.set_label(f"{load}%")
        help_text = f"Server load is at {load}%"
        self.set_tooltip_text(help_text)
        self.get_accessible().set_name(help_text)
        style_context = self.get_style_context()

        for cls in "signal-danger", "signal-warning", "signal-success":
            style_context.remove_class(cls)

        if load > 90:
            style_context.add_class("signal-danger")
        elif load > 75:
            style_context.add_class("signal-warning")
        else:
            style_context.add_class("signal-success")
