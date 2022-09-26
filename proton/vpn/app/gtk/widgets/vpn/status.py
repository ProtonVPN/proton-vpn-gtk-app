"""
This module defines the connection status widget.
"""
from proton.vpn.app.gtk import Gtk
from proton.vpn.app.gtk.controller import Controller
from proton.vpn.connection.enum import ConnectionStateEnum


class VPNConnectionStatusWidget(Gtk.Box):
    """Displays the current connection status."""

    def __init__(self, controller: Controller):
        super().__init__(spacing=10)
        self._controller = controller

        self.set_orientation(Gtk.Orientation.VERTICAL)
        self._connection_status_label = Gtk.Label(label="")
        self.add(self._connection_status_label)

    def connection_status_update(self, connection_status, vpn_server=None):
        """This method is called by VPNWidget whenever the VPN connection status changes."""
        self._update_status_label(
            connection_status.state,
            vpn_server
        )

    def _update_status_label(self, connection_state: ConnectionStateEnum, vpn_server=None):
        label = f"Status: {connection_state.name.lower()}"
        if vpn_server:
            preposition = "to" if connection_state in (
                ConnectionStateEnum.CONNECTING, ConnectionStateEnum.CONNECTED
            ) else "from"
            label = f"{label} {preposition} {vpn_server.servername}"
        self._connection_status_label.set_label(label)
