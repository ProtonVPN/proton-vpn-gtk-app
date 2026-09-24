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


class _MockAnnouncer:
    """Records what the screen reader would have been told, in order."""

    def __init__(self):
        self.messages = []
        self.urgent_messages = []

    def __call__(self, _widget, message, urgent=False):
        self.messages.append(message)
        if urgent:
            self.urgent_messages.append(message)


def _connecting_state(server_name="CH#1") -> states.Connecting:
    connection_state = states.Connecting()
    connection_state.context.reconnection = False
    connection_state.context.connection = Mock(server_name=server_name)
    connection_state.context.event = Mock()
    return connection_state


def _connected_state(server_name="CH#1") -> states.Connected:
    connection_state = states.Connected()
    connection_state.context.reconnection = False
    connection_state.context.connection = Mock(server_name=server_name)
    connection_state.context.event = Mock()
    return connection_state


def _free_tier_controller() -> Mock:
    controller_mock = make_controller(
        user_tier=TierEnum.FREE,
        server_selection_requires_upgrade=True,
        server_list=free_server_list(["CH", "JP", "NL", "US"]),
    )
    controller_mock.server_list.get_by_name = Mock(return_value=Mock(
        exit_country="ch", location="Zurich", features=[]
    ))
    return controller_mock


def test_disconnected_state_announces_the_status_and_the_intent():
    announcer = _MockAnnouncer()
    widget = VPNConnectionStatusWidget(make_controller(), Mock(), announce=announcer)

    widget.connection_status_update(_disconnected_state())

    assert announcer.messages == ["Unprotected. Fastest country"]


def test_connecting_state_announces_the_server_being_connected_to():
    """The details swap from the intent to the concrete target on Connecting,
    so the target is announced whether quick connected or picked by country.
    """
    announcer = _MockAnnouncer()
    widget = VPNConnectionStatusWidget(make_controller(), Mock(), announce=announcer)

    widget.connection_status_update(_connecting_state())

    assert announcer.messages == ["Connecting. Switzerland, Zurich - CH#1"]


def test_reaching_connected_does_not_repeat_the_server_just_announced():
    announcer = _MockAnnouncer()
    widget = VPNConnectionStatusWidget(make_controller(), Mock(), announce=announcer)

    widget.connection_status_update(_connecting_state())
    widget.connection_status_update(_connected_state())

    assert announcer.messages == [
        "Connecting. Switzerland, Zurich - CH#1",
        "Protected",
    ]


def test_replaying_an_unchanged_state_is_not_announced_again():
    """VPNWidget replays the current status on load and on server list
    updates.
    """
    announcer = _MockAnnouncer()
    widget = VPNConnectionStatusWidget(make_controller(), Mock(), announce=announcer)

    widget.connection_status_update(_connected_state())
    widget.connection_status_update(_connected_state())

    assert announcer.messages == ["Protected. Switzerland, Zurich - CH#1"]


def test_error_state_announces_the_error_detail_and_cuts_in():
    """Orca 49 onward honours the priority, so errors are sent as urgent."""
    announcer = _MockAnnouncer()
    widget = VPNConnectionStatusWidget(make_controller(), Mock(), announce=announcer)
    widget.connection_status_update(_connected_state())

    connection_state = states.Error()
    connection_state.context.reconnection = False
    connection_state.context.connection = Mock(server_name="CH#1")
    connection_state.context.event = events.AuthDenied(EventContext(connection=Mock()))

    widget.connection_status_update(connection_state)

    assert announcer.messages == [
        "Protected. Switzerland, Zurich - CH#1",
        "Connection error. Authentication denied",
    ]
    assert announcer.urgent_messages == ["Connection error. Authentication denied"]


def test_free_tier_announcement_omits_the_subtitle_the_summary_replaced():
    """The subtitle keeps its last value while the free-countries summary
    stands in for it, so the stale server name must not leak in.
    """
    announcer = _MockAnnouncer()
    widget = VPNConnectionStatusWidget(_free_tier_controller(), Mock(), announce=announcer)

    widget.connection_status_update(_connected_state())
    widget.connection_status_update(_disconnected_state())

    assert widget.connection_details_subtitle.get_text() == "Zurich - CH#1"
    assert announcer.messages[-1] == "Unprotected. Fastest free server"


def test_nothing_is_announced_once_the_user_has_logged_out():
    """Updates can still arrive via GLib.idle_add after logout, when the
    detail labels hold the previous session's server.
    """
    controller_mock = make_controller()
    announcer = _MockAnnouncer()
    widget = VPNConnectionStatusWidget(controller_mock, Mock(), announce=announcer)
    widget.connection_status_update(_connected_state())

    controller_mock.user_logged_in = False
    widget.connection_status_update(_disconnected_state())

    assert announcer.messages == ["Protected. Switzerland, Zurich - CH#1"]


@pytest.mark.parametrize("state_type", [states.Disconnecting, states.Disconnected])
def test_the_states_a_server_change_passes_through_are_not_announced(state_type):
    """A server change passes through both on its way to the new connection.
    Announcing them would say "Connecting" twice and claim the user is
    unprotected mid-change.
    """
    announcer = _MockAnnouncer()
    widget = VPNConnectionStatusWidget(make_controller(), Mock(), announce=announcer)
    widget.connection_status_update(_connected_state())

    intermediate = state_type()
    intermediate.context.reconnection = Mock(server_name="JP#2")
    intermediate.context.connection = Mock(server_name="CH#1")
    intermediate.context.event = Mock()
    widget.connection_status_update(intermediate)

    assert announcer.messages == ["Protected. Switzerland, Zurich - CH#1"]


def test_a_user_initiated_disconnect_is_still_announced():
    """Disconnecting with no reconnection pending is the user's own
    disconnect, not a step in a server change, so it is still announced.
    """
    announcer = _MockAnnouncer()
    widget = VPNConnectionStatusWidget(make_controller(), Mock(), announce=announcer)
    widget.connection_status_update(_connected_state())
    announcer.messages.clear()

    disconnecting = states.Disconnecting()
    disconnecting.context.reconnection = None
    disconnecting.context.connection = Mock(server_name="CH#1")
    disconnecting.context.event = Mock()
    widget.connection_status_update(disconnecting)
    widget.connection_status_update(_disconnected_state())

    assert announcer.messages == [
        "Disconnecting",
        "Unprotected. Fastest country",
    ]


def test_changing_server_announces_the_new_server_once():
    """The whole sequence, as the state machine produces it."""
    controller_mock = make_controller()
    announcer = _MockAnnouncer()
    widget = VPNConnectionStatusWidget(controller_mock, Mock(), announce=announcer)
    widget.connection_status_update(_connected_state())
    announcer.messages.clear()

    pending = Mock(server_name="JP#2")
    controller_mock.server_list.get_by_name.return_value = Mock(
        exit_country="jp", location="Tokyo", features=[]
    )
    for state_type in (states.Disconnecting, states.Disconnected):
        intermediate = state_type()
        intermediate.context.reconnection = pending
        intermediate.context.connection = Mock(server_name="CH#1")
        intermediate.context.event = Mock()
        widget.connection_status_update(intermediate)
    for state_type in (states.Connecting, states.Connected):
        state = state_type()
        state.context.reconnection = None
        state.context.connection = pending
        state.context.event = Mock()
        widget.connection_status_update(state)

    assert announcer.messages == [
        "Connecting. Japan, Tokyo - JP#2",
        "Protected",
    ]


@pytest.mark.parametrize("state_factory, expected", [
    (_disconnected_state, "Fastest country"),
    (_connecting_state, "Switzerland, Zurich - CH#1"),
    (_connected_state, "Switzerland, Zurich - CH#1"),
])
def test_accessible_details_feed_the_buttons_description(state_factory, expected):
    """The label already carries the state, so the description carries the
    server, or while disconnected what would be picked.
    """
    widget = VPNConnectionStatusWidget(make_controller(), Mock(), announce=_MockAnnouncer())

    widget.connection_status_update(state_factory())

    assert widget.accessible_details == expected


def test_update_status_does_not_announce_until_asked():
    announcer = _MockAnnouncer()
    widget = VPNConnectionStatusWidget(make_controller(), Mock(), announce=announcer)

    state = _connecting_state()
    widget.update_status(state)
    assert announcer.messages == []

    widget.announce_state_change(state)
    assert announcer.messages == ["Connecting. Switzerland, Zurich - CH#1"]


def test_reset_announcements_lets_the_same_state_be_announced_again():
    announcer = _MockAnnouncer()
    widget = VPNConnectionStatusWidget(make_controller(), Mock(), announce=announcer)

    widget.connection_status_update(_connected_state())
    widget.reset_announcements()
    widget.connection_status_update(_connected_state())

    assert announcer.messages == ["Protected. Switzerland, Zurich - CH#1"] * 2


def test_announcing_without_a_toplevel_window_is_a_no_op():
    """The real announcer runs here: a widget with no root window must be
    silently skipped rather than raise.
    """
    widget = VPNConnectionStatusWidget(make_controller(), Mock())

    widget.connection_status_update(_connected_state())

    assert widget.status_message == "Protected"


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


def test_nothing_is_announced_when_free_rescope_is_off():
    announcer = _MockAnnouncer()
    controller_mock = make_controller()
    controller_mock.feature_flags.get.return_value = False
    widget = VPNConnectionStatusWidget(controller_mock, Mock(), announce=announcer)

    widget.connection_status_update(_connected_state())

    assert announcer.messages == []
