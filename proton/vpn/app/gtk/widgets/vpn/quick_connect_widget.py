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
from proton.vpn.connection.states import State

from proton.vpn.app.gtk import Gtk
from proton.vpn.app.gtk.controller import Controller
from proton.vpn import logging

logger = logging.getLogger(__name__)


class QuickConnectWidget(Gtk.Box):
    """Widget handling the "Quick Connect" functionality."""
    def __init__(self, controller: Controller):
        super().__init__(spacing=10)
        self._controller = controller
        self._connection_state: State = None

        self.set_orientation(Gtk.Orientation.VERTICAL)
        self.connect_button = Gtk.Button(label="Quick Connect")
        self.connect_button.get_style_context().add_class("primary")
        self.connect_button.connect(
            "clicked", self._on_connect_button_clicked)
        self.connect_button.set_no_show_all(True)
        self.pack_start(self.connect_button, expand=False, fill=False, padding=0)
        self.disconnect_button = Gtk.Button(label="Disconnect")
        self.disconnect_button.get_style_context().add_class("danger")
        self.disconnect_button.connect(
            "clicked", self._on_disconnect_button_clicked)
        self.disconnect_button.set_no_show_all(True)
        self.pack_start(self.disconnect_button, expand=False, fill=False, padding=0)

    @property
    def connection_state(self):
        """Returns the current connection state."""
        return self._connection_state

    @connection_state.setter
    def connection_state(self, connection_state: State):
        """Sets the current connection state, updating the UI accordingly."""
        # pylint: disable=duplicate-code
        self._connection_state = connection_state

        # Update the UI according to the connection state.
        method = f"_on_connection_state_{type(connection_state).__name__.lower()}"
        if hasattr(self, method):
            getattr(self, method)()

    def connection_status_update(self, connection_state):
        """This method is called by VPNWidget whenever the VPN connection status changes."""
        self.connection_state = connection_state

    def _on_connection_state_disconnected(self):
        self.disconnect_button.hide()
        self.connect_button.show()

    def _on_connection_state_connecting(self):
        self.connect_button.hide()
        self.disconnect_button.set_label("Cancel Connection")
        self.disconnect_button.show()

    def _on_connection_state_connected(self):
        self.connect_button.hide()
        self.disconnect_button.set_label("Disconnect")
        self.disconnect_button.show()

    def _on_connection_state_disconnecting(self):
        pass

    def _on_connection_state_error(self):
        self.connect_button.hide()
        self.disconnect_button.set_label("Cancel Connection")
        self.disconnect_button.show()

    def _on_connect_button_clicked(self, _):
        logger.info("Connect to fastest server", category="ui.tray", event="connect")
        self._controller.connect_to_fastest_server()

    def _on_disconnect_button_clicked(self, _):
        logger.info("Disconnect from VPN", category="ui", event="disconnect")
        self._controller.disconnect()
