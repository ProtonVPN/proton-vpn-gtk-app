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
from gi.repository import GLib
from proton.vpn.connection import states

from proton.vpn.app.gtk import Gtk
from proton.vpn.app.gtk.controller import Controller
from proton.vpn.app.gtk.translator import C_
from proton.vpn.app.gtk.utils.safe_signal_connect import safe_signal_connect
from proton.vpn import logging

logger = logging.getLogger(__name__)


class QuickConnectWidget(Gtk.Box):  # pylint: disable=too-many-instance-attributes
    """Widget handling the "Quick Connect" functionality."""
    CHANGE_SERVER_LABEL = C_("button", "Change server")

    def __init__(self, controller: Controller):
        super().__init__(spacing=10)
        self.set_name("quick-connect-widget")
        self._controller = controller
        self._connection_state: states.State = None
        # Whether the "Change server" button is ever shown for this user.
        self._show_change_server = controller.server_selection_requires_upgrade

        self.set_orientation(Gtk.Orientation.VERTICAL)
        self.connect_button = Gtk.Button(label=C_("button", "Connect"))
        self.connect_button.add_css_class("primary")
        safe_signal_connect(
            self.connect_button,
            "clicked", self._on_connect_button_clicked)
        self.connect_button.set_visible(False)
        self.append(self.connect_button)
        self.disconnect_button = Gtk.Button(label=C_("button", "Disconnect"))
        self.disconnect_button.add_css_class("danger")
        safe_signal_connect(
            self.disconnect_button,
            "clicked", self._on_disconnect_button_clicked)
        self.disconnect_button.set_visible(False)
        self.append(self.disconnect_button)
        self.change_server_button = Gtk.Button(
            label=QuickConnectWidget.CHANGE_SERVER_LABEL
        )
        self.change_server_button.add_css_class("secondary")
        safe_signal_connect(
            self.change_server_button,
            "clicked", self._on_change_server_button_clicked)
        self.change_server_button.set_sensitive(False)
        self.change_server_revealer = Gtk.Revealer()
        self.change_server_revealer.set_child(self.change_server_button)
        # Appended last so it renders below whichever of the connect/disconnect
        # buttons is showing: Gtk.Box skips hidden children, so the hidden one
        # costs neither height nor spacing.
        self.append(self.change_server_revealer)

    @property
    def connection_state(self):
        """Returns the current connection state."""
        return self._connection_state

    @connection_state.setter
    def connection_state(self, connection_state: states.State):
        """Sets the current connection state, updating the UI accordingly."""
        # pylint: disable=duplicate-code
        self._connection_state = connection_state

        # Update the UI according to the connection state.
        if isinstance(connection_state, states.Disconnected) \
                and not connection_state.context.reconnection:
            self._on_connection_state_disconnected()
        elif isinstance(connection_state, states.Connecting):
            self._on_connection_state_connecting()
        elif isinstance(connection_state, states.Connected):
            self._on_connection_state_connected()
        elif isinstance(connection_state, states.Disconnecting):
            self._on_connection_state_disconnecting()
        elif isinstance(connection_state, states.Error):
            self._on_connection_state_error()

    def connection_status_update(self, connection_state):
        """This method is called by VPNWidget whenever the VPN connection status changes."""
        self.connection_state = connection_state

    def _on_connection_state_disconnected(self):
        self.disconnect_button.set_visible(False)
        self.connect_button.set_visible(True)
        self.change_server_revealer.set_reveal_child(False)
        self.change_server_button.set_sensitive(False)

    def _on_connection_state_connecting(self):
        self.connect_button.set_visible(False)
        self.disconnect_button.set_label(C_("button", "Cancel Connection"))
        self.disconnect_button.set_visible(True)
        self.change_server_revealer.set_reveal_child(self._show_change_server)
        # There is no established connection to change away from yet.
        self.change_server_button.set_sensitive(False)

    def _on_connection_state_connected(self):
        self.connect_button.set_visible(False)
        self.disconnect_button.set_label(C_("button", "Disconnect"))
        self.disconnect_button.set_visible(True)
        self.change_server_revealer.set_reveal_child(self._show_change_server)
        self.change_server_button.set_sensitive(self._show_change_server)

    def _on_connection_state_disconnecting(self):
        # Visibility is deliberately left alone so the button doesn't flicker
        # while switching servers, but it must not be clickable while the
        # current connection is being torn down: a click here would turn a
        # user-requested disconnect into a reconnection.
        self.change_server_button.set_sensitive(False)

    def _on_connection_state_error(self):
        self.connect_button.set_visible(False)
        self.disconnect_button.set_label(C_("button", "Cancel Connection"))
        self.disconnect_button.set_visible(True)
        self.change_server_revealer.set_reveal_child(False)
        self.change_server_button.set_sensitive(False)

    def _on_connect_button_clicked(self, _):
        logger.info("Connect to fastest server", category="ui.tray", event="connect")
        future = self._controller.connect_to_fastest_server()
        future.add_done_callback(lambda f: GLib.idle_add(f.result))  # bubble up exceptions if any.

    def _on_disconnect_button_clicked(self, _):
        logger.info("Disconnect from VPN", category="ui", event="disconnect")
        future = self._controller.disconnect()
        future.add_done_callback(lambda f: GLib.idle_add(f.result))  # bubble up exceptions if any.

    def _on_change_server_button_clicked(self, _):
        logger.info("Change to another server", category="ui", event="change_server")
        future = self._controller.change_server()
        future.add_done_callback(lambda f: GLib.idle_add(f.result))  # bubble up exceptions if any.
