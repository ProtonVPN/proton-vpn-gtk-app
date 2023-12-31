"""
This module defines the connection status widget.


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
from proton.vpn.app.gtk import Gtk
from proton.vpn.connection import events, states


class VPNConnectionStatusWidget(Gtk.Box):
    """Displays the current connection status."""

    def __init__(self):
        super().__init__(spacing=10)

        self.set_orientation(Gtk.Orientation.VERTICAL)
        self._connection_status_label = Gtk.Label(label="")
        self.add(self._connection_status_label)

    @property
    def status_message(self) -> str:
        """Returns the connection status message being displayed to the user."""
        return self._connection_status_label.get_label()

    def connection_status_update(self, connection_status):
        """This method is called by VPNWidget whenever the VPN connection status changes."""
        self._update_connection_status_label(connection_status)

    def _update_connection_status_label(self, connection_status):
        connection = connection_status.context.connection

        label = ""
        if isinstance(connection_status, states.Disconnected):
            label = "You are disconnected"
        elif isinstance(connection_status, states.Connecting):
            label = f"Connecting to {connection.server_name}..."
        elif isinstance(connection_status, states.Connected):
            label = f"You are connected to {connection.server_name}"
        elif isinstance(connection_status, states.Disconnecting):
            label = f"Disconnecting from {connection.server_name}..."
        elif isinstance(connection_status, states.Error):
            last_connection_event = connection_status.context.event
            label = "Connection error"
            if isinstance(last_connection_event, events.TunnelSetupFailed):
                label = f"{label}: tunnel setup failed"
            elif isinstance(last_connection_event, events.AuthDenied):
                label = f"{label}: authentication denied"
            elif isinstance(last_connection_event, events.Timeout):
                label = f"{label}: timeout"
            elif isinstance(last_connection_event, events.DeviceDisconnected):
                label = f"{label}: device disconnected"

        self._connection_status_label.set_label(label)
