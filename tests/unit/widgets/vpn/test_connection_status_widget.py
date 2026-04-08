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
from unittest.mock import Mock, patch

from proton.vpn.connection import states, events
from proton.vpn.connection.events import EventContext

from proton.vpn.session.servers import TierEnum

from proton.vpn.app.gtk.widgets.vpn.connection_status_widget import VPNConnectionStatusWidget, SPLIT_TUNNELING_APP_RESTART_MESSAGE
import pytest


@pytest.mark.parametrize("connection_state_type, last_event_type, expected_message", [
    (states.Disconnected, None, "Unprotected"),
    (states.Connecting, None, "Connecting..."),
    (states.Connected, None, "Protected"),
    (states.Disconnecting, None, "Disconnecting..."),
    (states.Error, None, "Connection error"),
    (states.Error, events.TunnelSetupFailed, "Connection error"),
    (states.Error, events.AuthDenied, "Connection error"),
    (states.Error, events.Timeout, "Connection error"),
    (states.Error, events.DeviceDisconnected, "Connection error"),
    (states.Error, events.MaximumSessionsReached, "Connection error"),
])
def test_connection_status_update_updates_status_message(connection_state_type, last_event_type, expected_message):
    mock_notifications = Mock()
    controller_mock = Mock()
    controller_mock.server_list.get_by_name.return_value = Mock(
        exit_country="ch",
        exit_country_name="Switzerland",
        location="Zurich",
        features=[]
    )
    vpn_status_widget = VPNConnectionStatusWidget(
        controller_mock,
        mock_notifications
    )

    connection_state = connection_state_type()
    last_event = Mock()
    if last_event_type:
        last_event = last_event_type(EventContext(connection=Mock()))

    connection_state.context.event = last_event
    connection_state.context.connection = Mock()
    connection_state.context.connection.server_name = "CH#1"

    vpn_status_widget.connection_status_update(connection_state)

    if isinstance(connection_state.context.event, events.MaximumSessionsReached):
        mock_notifications.show_error_dialog.assert_called_once_with(
            message=vpn_status_widget.MAXIMUM_SESSIONS_ERROR,
            title="Connection error: session limit reached"
        )

    assert vpn_status_widget.status_message == expected_message


def test_connection_status_update_notifies_user_when_in_connected_state_and_split_tunneling_is_enabled():
    controller_mock = Mock(name="controller")
    controller_mock.get_setting_attr.return_value = True  # Simulate split tunneling being enabled
    controller_mock.server_list.get_by_name.return_value = Mock(
        exit_country="ch",
        exit_country_name="Switzerland",
        location="Zurich",
        features=[]
    )

    mock_notifications = Mock()
    vpn_status_widget = VPNConnectionStatusWidget(
        controller_mock,
        mock_notifications
    )

    connection_state = states.Connected()

    connection_state.context.event = Mock()
    connection_state.context.connection = Mock()
    connection_state.context.connection.server_name = "CH#1"

    vpn_status_widget.connection_status_update(connection_state)

    mock_notifications.show_info_message.assert_called_once_with(
        message=SPLIT_TUNNELING_APP_RESTART_MESSAGE
    )


@pytest.mark.parametrize("connection_state_type, reconnection, expected_subtitle", [
    (states.Connected, False, "Zurich - CH#1"),
    (states.Connecting, False, "Zurich - CH#1"),
    (states.Disconnecting, False, "Zurich - CH#1"),
    (states.Error, False, "Zurich - CH#1"),
    (states.Disconnected, True, "Zurich - CH#1"),    # reconnection ongoing: show server details
    (states.Disconnected, False, ""),  # no server details
])
def test_connection_status_update_shows_server_details_except_on_disconnected_state_if_no_reconnection_ongoing(
    connection_state_type, reconnection, expected_subtitle
):
    mock_notifications = Mock()
    controller_mock = Mock()
    controller_mock.user_tier = TierEnum.PLUS
    controller_mock.server_list.get_by_name.return_value = Mock(
        exit_country="ch",
        exit_country_name="Switzerland",
        location="Zurich",
        features=[]
    )
    vpn_status_widget = VPNConnectionStatusWidget(controller_mock, mock_notifications)

    connection_state = connection_state_type()
    connection_state.context.reconnection = reconnection
    connection_state.context.connection = Mock()
    connection_state.context.connection.server_name = "CH#1"
    connection_state.context.event = Mock()

    vpn_status_widget.connection_status_update(connection_state)

    assert vpn_status_widget._connection_details_subtitle.get_text() == expected_subtitle


def test_connection_status_update_shows_fastest_free_server_message_on_disconnected_state_when_user_is_free():
    controller_mock = Mock()
    controller_mock.user_tier = TierEnum.FREE
    vpn_status_widget = VPNConnectionStatusWidget(controller_mock, Mock())

    connection_state = states.Disconnected()
    connection_state.context.reconnection = False
    connection_state.context.connection = None
    connection_state.context.event = Mock()

    vpn_status_widget.connection_status_update(connection_state)

    assert vpn_status_widget._connection_details_title.get_text() == "Fastest free server"
    assert vpn_status_widget._connection_details_subtitle.get_text() == "Auto-selected from free locations"


def test_connection_status_update_shows_fastest_server_message_on_disconnected_state_when_user_is_paid():
    controller_mock = Mock()
    controller_mock.user_tier = TierEnum.PLUS
    vpn_status_widget = VPNConnectionStatusWidget(controller_mock, Mock())

    connection_state = states.Disconnected()
    connection_state.context.reconnection = False
    connection_state.context.connection = None
    connection_state.context.event = Mock()

    vpn_status_widget.connection_status_update(connection_state)

    assert vpn_status_widget._connection_details_title.get_text() == "Fastest country"
    assert vpn_status_widget._connection_details_subtitle.get_text() == ""
