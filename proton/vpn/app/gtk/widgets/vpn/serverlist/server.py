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
from typing import List

from gi.repository import Pango, Atk
from proton.vpn.servers.enums import ServerFeatureEnum

from proton.vpn.app.gtk.utils import accessibility
from proton.vpn.app.gtk.utils.search import normalize
from proton.vpn.connection.enum import ConnectionStateEnum
from proton.vpn.servers.server_types import LogicalServer
from proton.vpn.app.gtk.widgets.vpn.serverlist.icons import \
    UnderMaintenanceIcon, SmartRoutingIcon, StreamingIcon, \
    P2PIcon, TORIcon
from proton.vpn.app.gtk import Gtk
from proton.vpn import logging

from proton.vpn.app.gtk.controller import Controller

logger = logging.getLogger(__name__)


class ServerLoad(Gtk.Label):
    """Displays the current CPU load of a server."""
    def __init__(self, load: int):
        super().__init__(label=f"{load}%")
        self.set_name("server-load")
        help_text = f"Server load is at {load}%"
        self.set_tooltip_text(help_text)
        self.get_accessible().set_name(help_text)
        style_context = self.get_style_context()
        if load > 90:
            style_context.add_class("signal-danger")
        elif load > 75:
            style_context.add_class("signal-warning")
        else:
            style_context.add_class("signal-success")


class ServerRow(Gtk.Box):
    """Displays a single server as a row in the server list."""
    def __init__(self, server: LogicalServer, user_tier: int, controller: Controller):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL)
        self._server = server
        self._user_tier = user_tier
        self._controller = controller
        self._connection_state: ConnectionStateEnum = None
        self._icons_displayed = []
        self._connect_button = None

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

        if self.under_maintenance:
            under_maintenance_icon = UnderMaintenanceIcon(self._server.name)
            self.pack_end(
                under_maintenance_icon,
                expand=False, fill=False, padding=10
            )
            self._icons_displayed.append(under_maintenance_icon)
            self._server_label.set_property("sensitive", False)
            return

        if self.upgrade_required:
            button = self._build_upgrade_link_button()
            self.pack_end(button, expand=False, fill=False, padding=10)
        else:
            self._connect_button = self._build_connect_button()
            button = self._connect_button
            self.pack_end(self._connect_button, expand=False, fill=False, padding=10)

        button_relationships = [(self._server_label, Atk.RelationType.LABELLED_BY)]

        server_load = ServerLoad(self._server.load)
        button_relationships.append((server_load, Atk.RelationType.DESCRIBED_BY))
        self.pack_end(server_load, expand=False, fill=False, padding=10)

        server_row_icons = []
        smart_routing = self._server.host_country is not None
        if smart_routing:
            server_row_icons.append(SmartRoutingIcon())

        server_feature_icons = self._build_server_feature_icons()
        server_row_icons.extend(server_feature_icons)
        for icon in server_row_icons:
            button_relationships.append((icon, Atk.RelationType.DESCRIBED_BY))
            self.pack_end(icon, expand=False, fill=False, padding=0)
            self._icons_displayed.append(icon)

        accessibility.add_widget_relationships(button, button_relationships)

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
        self._controller.connect_to_server(self._server.name)

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
    def server_tier(self) -> str:
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
        return bool(self._connect_button)

    def is_icon_displayed(self, icon_class):
        """Returns True if an instance of the specified icon class is displayed
        or False otherwise."""
        filtered_icons = [
            icon for icon in self._icons_displayed
            if isinstance(icon, icon_class)
        ]
        return bool(filtered_icons)
