"""
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
from unittest.mock import Mock

from proton.vpn.connection import states, events
from proton.vpn.connection.events import EventContext

from proton.vpn.app.gtk.widgets.vpn.connection_status_widget import VPNConnectionStatusWidget
from proton.vpn.app.gtk.widgets.main.loading_widget import OverlayWidget
import pytest


@pytest.mark.parametrize("connection_state_type, last_event_type, expected_message", [
    (states.Disconnected, None, "You are disconnected"),
    (states.Connecting, None, "Connecting to CH#1"),
    (states.Connected, None, "You are connected to CH#1"),
    (states.Disconnecting, None, "Disconnecting from CH#1"),
    (states.Error, None, "Connection error"),
    (states.Error, events.TunnelSetupFailed, "Connection error: tunnel setup failed"),
    (states.Error, events.AuthDenied, "Connection error: authentication denied"),
    (states.Error, events.Timeout, "Connection error: timeout"),
    (states.Error, events.DeviceDisconnected, "Connection error: device disconnected"),
])
def test_vpn_connection_status_widget(connection_state_type, last_event_type, expected_message):
    overlay_widget_mock = Mock()
    vpn_status_widget = VPNConnectionStatusWidget(Mock(), overlay_widget_mock)

    connection_state = connection_state_type()
    last_event = None
    if last_event_type:
        last_event = last_event_type(EventContext(connection=Mock()))

    connection_state.context.event = last_event
    connection_state.context.connection = Mock()
    connection_state.context.connection.server_name = "CH#1"

    vpn_status_widget.connection_status_update(connection_state)

    # When we are connection we only display the overlay and we don't update the label
    if isinstance(connection_state, states.Connecting):
        overlay_widget_mock.show.assert_called_once()
    else:
        assert vpn_status_widget.status_message == expected_message
