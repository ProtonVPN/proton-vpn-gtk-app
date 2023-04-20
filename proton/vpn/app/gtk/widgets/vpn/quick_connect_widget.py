"""
This module defines the Quick Connect widget.


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
from proton.vpn.connection.enum import ConnectionStateEnum
from proton.vpn.app.gtk import Gtk
from proton.vpn.app.gtk.controller import Controller
from proton.vpn import logging

logger = logging.getLogger(__name__)


class QuickConnectWidget(Gtk.Box):
    """Widget handling the "Quick Connect" functionality."""
    def __init__(self, controller: Controller):
        super().__init__(spacing=10)
        self._controller = controller
        self._connection_state: ConnectionStateEnum = None

        self.set_orientation(Gtk.Orientation.VERTICAL)
        self._connect_button = Gtk.Button(label="Quick Connect")
        self._connect_button.get_style_context().add_class("primary")
        self._connect_button.connect(
            "clicked", self._on_connect_button_clicked)
        self._connect_button.set_no_show_all(True)
        self.pack_start(self._connect_button, expand=False, fill=False, padding=0)
        self._disconnect_button = Gtk.Button(label="Disconnect")
        self._disconnect_button.get_style_context().add_class("danger")
        self._disconnect_button.connect(
            "clicked", self._on_disconnect_button_clicked)
        self._disconnect_button.set_no_show_all(True)
        self.pack_start(self._disconnect_button, expand=False, fill=False, padding=0)

    def connect_button_click(self):
        """Clicks the connect button.
        This method was made available for tests.
        """
        self._connect_button.clicked()

    def disconnect_button_click(self):
        """Clicks the disconnect button.
        This method was made available for tests.
        """
        self._disconnect_button.clicked()

    @property
    def connection_state(self):
        """Returns the current connection state."""
        return self._connection_state

    @connection_state.setter
    def connection_state(self, connection_state: ConnectionStateEnum):
        """Sets the current connection state, updating the UI accordingly."""
        # pylint: disable=duplicate-code
        self._connection_state = connection_state

        # Update the UI according to the connection state.
        method = f"_on_connection_state_{connection_state.name.lower()}"
        if hasattr(self, method):
            getattr(self, method)()

    def connection_status_update(self, connection_state):
        """This method is called by VPNWidget whenever the VPN connection status changes."""
        self.connection_state = connection_state.type

    def _on_connection_state_connected(self):
        self._connect_button.hide()
        self._disconnect_button.set_sensitive(True)
        self._disconnect_button.show()

    def _on_connection_state_connecting(self):
        self._connect_button.set_sensitive(False)

    def _on_connection_state_disconnecting(self):
        self._disconnect_button.set_sensitive(False)

    def _on_connection_state_disconnected(self):
        self._disconnect_button.hide()
        self._connect_button.set_sensitive(True)
        self._connect_button.show()

    def _on_connection_state_error(self):
        self._on_connection_state_disconnected()

    def _on_connect_button_clicked(self, _):
        logger.info("Connect to fastest server", category="ui.tray", event="connect")
        self._connect_button.set_sensitive(False)
        self._controller.connect_to_fastest_server()

    def _on_disconnect_button_clicked(self, _):
        logger.info("Disconnect from VPN", category="ui", event="disconnect")
        self._disconnect_button.set_sensitive(False)
        self._controller.disconnect()
