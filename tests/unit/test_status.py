from unittest.mock import Mock

from proton.vpn.connection import states, events

from proton.vpn.app.gtk.widgets.vpn.status import VPNConnectionStatusWidget
import pytest


@pytest.mark.parametrize("connection_status, last_event, expected_message", [
    (states.Disconnected(), None, "You are disconnected"),
    (states.Connecting(), None, "Connecting to CH#1..."),
    (states.Connected(), None, "You are connected to CH#1"),
    (states.Disconnecting(), None, "Disconnecting from CH#1..."),
    (states.Error(), None, "Connection error"),
    (states.Error(), events.TunnelSetupFailed(), "Connection error: tunnel setup failed"),
    (states.Error(), events.AuthDenied(), "Connection error: authentication denied"),
    (states.Error(), events.Timeout(), "Connection error: timeout"),
    (states.Error(), events.DeviceDisconnected(), "Connection error: device disconnected"),
])
def test_vpn_connection_status_widget(connection_status, last_event, expected_message):
    vpn_status_widget = VPNConnectionStatusWidget()

    connection_status.context.event = last_event
    connection_status.context.connection = Mock()
    connection_status.context.connection.server_name = "CH#1"

    vpn_status_widget.connection_status_update(connection_status)

    assert vpn_status_widget.status_message == expected_message
