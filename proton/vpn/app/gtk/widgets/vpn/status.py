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

    def connection_status_update(self, connection_status):
        """This method is called by VPNWidget whenever the VPN connection status changes."""
        connection = connection_status.context.connection
        self._update_status_label(
            connection_status.state,
            connection.server_name if connection else None
        )

    def _update_status_label(self, connection_state: ConnectionStateEnum, server_name: str):
        label = f"Status: {connection_state.name.lower()}"
        if connection_state in (
            ConnectionStateEnum.CONNECTING, ConnectionStateEnum.CONNECTED
        ):
            label = f"{label} to {server_name}"
        self._connection_status_label.set_label(label)
