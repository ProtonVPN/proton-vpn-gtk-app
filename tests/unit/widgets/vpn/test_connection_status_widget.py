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

from proton.vpn.app.gtk.widgets.vpn.connection_status_widget import (
    VPNConnectionStatusWidget,
    SPLIT_TUNNELING_APP_RESTART_MESSAGE,
    PROTUN_ONLY_FREE_USER_MESSAGE,
)
import pytest

from tests.unit.testing_utils import free_server_list


def make_controller(**overrides) -> Mock:
    """A controller reporting a paid, logged-in user, connected to CH#1."""
    controller_mock = Mock()
    controller_mock.user_logged_in = True
    controller_mock.user_tier = TierEnum.PLUS
    controller_mock.server_selection_requires_upgrade = False
    controller_mock.server_list.get_by_name.return_value = Mock(
        exit_country="ch",
        exit_country_name="Switzerland",
        location="Zurich",
        features=[]
    )
    for name, value in overrides.items():
        setattr(controller_mock, name, value)
    return controller_mock


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
    controller_mock = make_controller()
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


@pytest.mark.parametrize("user_tier, flag_enabled, expected", [
    (TierEnum.FREE, True, True),
    (TierEnum.FREE, False, False),
    (TierEnum.PLUS, True, False),
])
def test_protun_only_free_user_notification(user_tier, flag_enabled, expected):
    controller_mock = Mock(name="controller")
    controller_mock.get_setting_attr.return_value = False  # split tunneling off
    controller_mock.user_tier = user_tier
    controller_mock.feature_flags.get.return_value = flag_enabled
    controller_mock.server_list.get_by_name.return_value = Mock(
        exit_country="ch",
        exit_country_name="Switzerland",
        location="Zurich",
        features=[]
    )

    mock_notifications = Mock()
    widget = VPNConnectionStatusWidget(controller_mock, mock_notifications)

    connection_state = states.Connected()
    connection_state.context.connection = Mock(server_name="CH#1")
    widget.connection_status_update(connection_state)

    shown = any(
        call.kwargs.get("message") == PROTUN_ONLY_FREE_USER_MESSAGE
        for call in mock_notifications.show_info_message.call_args_list
    )
    assert shown is expected


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
    controller_mock = make_controller()
    vpn_status_widget = VPNConnectionStatusWidget(controller_mock, mock_notifications)

    connection_state = connection_state_type()
    connection_state.context.reconnection = reconnection
    connection_state.context.connection = Mock()
    connection_state.context.connection.server_name = "CH#1"
    connection_state.context.event = Mock()

    vpn_status_widget.connection_status_update(connection_state)

    assert vpn_status_widget.connection_details_subtitle.get_text() == expected_subtitle


def test_connection_status_update_shows_fastest_server_message_on_disconnected_state_when_user_is_paid():
    controller_mock = make_controller()
    vpn_status_widget = VPNConnectionStatusWidget(controller_mock, Mock())

    connection_state = states.Disconnected()
    connection_state.context.reconnection = False
    connection_state.context.connection = None
    connection_state.context.event = Mock()

    vpn_status_widget.connection_status_update(connection_state)

    assert vpn_status_widget.connection_details_title.get_text() == "Fastest country"
    assert vpn_status_widget.connection_details_subtitle.get_text() == ""
    assert vpn_status_widget.free_countries_summary.get_visible() is False


def _disconnected_state() -> states.Disconnected:
    connection_state = states.Disconnected()
    connection_state.context.reconnection = False
    connection_state.context.connection = None
    connection_state.context.event = Mock()
    return connection_state


def test_free_user_sees_the_countries_summary_instead_of_the_subtitle():
    controller_mock = make_controller(
        user_tier=TierEnum.FREE,
        server_selection_requires_upgrade=True,
        server_list=free_server_list(["CH", "JP", "NL", "US"]),
    )
    vpn_status_widget = VPNConnectionStatusWidget(controller_mock, Mock())

    vpn_status_widget.connection_status_update(_disconnected_state())

    assert vpn_status_widget.connection_details_title.get_text() == "Fastest free server"
    assert vpn_status_widget.free_countries_summary.get_visible() is True
    assert vpn_status_widget.connection_details_subtitle.get_visible() is False


def test_free_countries_summary_is_hidden_once_connected():
    controller_mock = make_controller(
        user_tier=TierEnum.FREE,
        server_selection_requires_upgrade=True,
        server_list=free_server_list(["CH", "JP", "NL", "US"]),
    )
    controller_mock.server_list.get_by_name = Mock(return_value=Mock(
        exit_country="ch", location="Zurich", features=[]
    ))
    vpn_status_widget = VPNConnectionStatusWidget(controller_mock, Mock())
    vpn_status_widget.connection_status_update(_disconnected_state())
    assert vpn_status_widget.free_countries_summary.get_visible() is True

    connected = states.Connected()
    connected.context.reconnection = False
    connected.context.connection = Mock(server_name="CH#1")
    vpn_status_widget.connection_status_update(connected)

    assert vpn_status_widget.free_countries_summary.get_visible() is False
    assert vpn_status_widget.connection_details_subtitle.get_visible() is True


def test_summary_appears_once_the_session_reports_a_free_plan():
    """The plan lands after this widget is constructed, so what it implies for
    the summary has to be read on each update rather than cached.
    """
    controller_mock = make_controller(
        user_tier=TierEnum.PLUS,
        server_list=free_server_list(["CH", "JP", "NL", "US"]),
    )
    vpn_status_widget = VPNConnectionStatusWidget(controller_mock, Mock())
    vpn_status_widget.connection_status_update(_disconnected_state())
    assert vpn_status_widget.free_countries_summary.get_visible() is False

    controller_mock.user_tier = TierEnum.FREE
    controller_mock.server_selection_requires_upgrade = True
    vpn_status_widget.connection_status_update(_disconnected_state())

    assert vpn_status_widget.free_countries_summary.get_visible() is True


# ===========================================================================
# FreeRescope rollout. Delete everything below when the flag retires: free
# tier then always requires an upgrade to select a server, so a free user
# seeing the auto-selected subtitle becomes an impossible state.
# ===========================================================================

def test_free_tier_without_free_rescope_keeps_the_auto_selected_subtitle():
    """Free tier with the flag off: server selection doesn't require an
    upgrade, so the summary gives way to the subtitle it replaces.
    """
    controller_mock = Mock()
    controller_mock.user_logged_in = True
    controller_mock.user_tier = TierEnum.FREE
    controller_mock.server_selection_requires_upgrade = False
    vpn_status_widget = VPNConnectionStatusWidget(controller_mock, Mock())

    vpn_status_widget.connection_status_update(_disconnected_state())

    assert vpn_status_widget.connection_details_title.get_text() == "Fastest free server"
    assert vpn_status_widget.connection_details_subtitle.get_text() \
        == "Auto-selected from free locations"
    assert vpn_status_widget.connection_details_subtitle.get_visible() is True
    assert vpn_status_widget.free_countries_summary.get_visible() is False
