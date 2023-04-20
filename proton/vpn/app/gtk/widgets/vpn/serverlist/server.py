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
from gi.repository import Pango

from proton.vpn.app.gtk.utils.search import normalize
from proton.vpn.connection.enum import ConnectionStateEnum
from proton.vpn.servers.server_types import LogicalServer
from proton.vpn.app.gtk.widgets.vpn.serverlist.under_maintenance import UnderMaintenance
from proton.vpn.app.gtk import Gtk
from proton.vpn import logging

from proton.vpn.app.gtk.controller import Controller

logger = logging.getLogger(__name__)


class ServerRow(Gtk.Box):
    """Displays a single server as a row in the server list."""
    def __init__(self, server: LogicalServer, user_tier: int, controller: Controller):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL)
        self._server = server
        self._user_tier = user_tier
        self._controller = controller
        self._connection_state: ConnectionStateEnum = None
        self._under_maintenance_icon = None
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

        load_label = Gtk.Label(label=f"{self._server.load}%")
        self.pack_start(
            load_label,
            expand=False, fill=False, padding=10
        )
        if self.under_maintenance:
            self._under_maintenance_icon = UnderMaintenance(self._server.name)
            self.pack_end(
                self._under_maintenance_icon,
                expand=False, fill=False, padding=10
            )
            self._server_label.set_property("sensitive", False)
            load_label.set_property("sensitive", False)
            return

        if self.upgrade_required:
            upgrade_button = Gtk.LinkButton.new_with_label("Upgrade")
            upgrade_button.set_tooltip_text(f"Upgrade to connect to {self.server_label}")
            upgrade_button.set_uri("https://account.protonvpn.com/")
            self.pack_end(upgrade_button, expand=False, fill=False, padding=10)
        else:
            self._connect_button = Gtk.Button(label="Connect")
            self._connect_button.set_tooltip_text(f"Connect to {self.server_label}")
            self._connect_button.connect("clicked", self._on_connect_button_clicked)
            self._connect_button.get_style_context().add_class("secondary")
            self.pack_end(self._connect_button, expand=False, fill=False, padding=10)

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

    @property
    def is_under_maintenance_icon_visible(self) -> bool:
        """Returns if the under maintenance icon is visible.
        This method was made available for tests."""
        return bool(self._under_maintenance_icon)
