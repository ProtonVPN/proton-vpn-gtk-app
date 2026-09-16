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
import gc
import weakref
from unittest.mock import Mock

import pytest
from gi.repository import GLib

from proton.vpn.app.gtk import Gtk
from proton.vpn.app.gtk.widgets.vpn.quick_connect_widget import QuickConnectWidget
from proton.vpn.connection.states import \
    Disconnected, \
    Connected, \
    Connecting, \
    Disconnecting, \
    Error, \
    StateContext

from tests.unit.testing_utils import process_gtk_events, run_main_loop


@pytest.mark.parametrize("connection_state, connect_button_visible, disconnect_button_visible, disconnect_button_label", [
    (Disconnected(), True, False, None),
    (Connecting(), False, True, "Cancel Connection"),
    (Connected(), False, True, "Disconnect"),
    (Error(), False, True, "Cancel Connection")
])
def test_quick_connect_widget_changes_button_according_to_connection_state_changes(
        connection_state, connect_button_visible, disconnect_button_visible, disconnect_button_label
):
    quick_connect_widget = QuickConnectWidget(controller=Mock())
    window = Gtk.Window()
    window.set_child(quick_connect_widget)
    main_loop = GLib.MainLoop()

    def run():
        window.present()

        quick_connect_widget.connection_status_update(connection_state)

        try:
            assert quick_connect_widget.connection_state is connection_state
            assert quick_connect_widget.connect_button.get_visible() is connect_button_visible
            assert quick_connect_widget.disconnect_button.get_visible() is disconnect_button_visible
            if disconnect_button_label:
                assert quick_connect_widget.disconnect_button.get_label() == disconnect_button_label
        finally:
            main_loop.quit()

    GLib.idle_add(run)
    run_main_loop(main_loop)


def test_quick_connect_widget_connects_to_fastest_server_when_connect_button_is_clicked():
    controller_mock = Mock()
    quick_connect_widget = QuickConnectWidget(controller=controller_mock)

    quick_connect_widget.connect_button.emit("clicked")
    process_gtk_events()

    controller_mock.connect_to_fastest_server.assert_called_once()


def test_quick_connect_widget_disconnects_from_current_server_when_disconnect_is_clicked():
    controller_mock = Mock()
    quick_connect_widget = QuickConnectWidget(controller=controller_mock)

    quick_connect_widget.disconnect_button.emit("clicked")
    process_gtk_events()

    controller_mock.disconnect.assert_called_once()


@pytest.mark.parametrize("connection_state, change_server_button_visible", [
    (Disconnected(), False),
    (Connecting(), True),
    (Connected(), True),
    (Error(), False),
])
def test_quick_connect_widget_shows_change_server_button_only_while_connecting_or_connected(
        connection_state, change_server_button_visible
):
    controller_mock = Mock()
    controller_mock.server_selection_requires_upgrade = True
    quick_connect_widget = QuickConnectWidget(controller=controller_mock)

    quick_connect_widget.connection_status_update(connection_state)

    assert quick_connect_widget.change_server_revealer.get_reveal_child() \
        is change_server_button_visible


def test_quick_connect_widget_never_shows_change_server_button_when_upgrade_is_not_required():
    controller_mock = Mock()
    controller_mock.server_selection_requires_upgrade = False
    quick_connect_widget = QuickConnectWidget(controller=controller_mock)

    quick_connect_widget.connection_status_update(Connected())

    assert quick_connect_widget.change_server_revealer.get_reveal_child() is False


@pytest.mark.parametrize("connection_state, change_server_button_sensitive", [
    (Disconnected(), False),
    (Disconnected(StateContext(reconnection=Mock())), False),
    (Connecting(), False),
    (Connected(), True),
    (Disconnecting(), False),
    (Error(), False),
])
def test_quick_connect_widget_enables_change_server_button_only_while_connected(
        connection_state, change_server_button_sensitive
):
    controller_mock = Mock()
    controller_mock.server_selection_requires_upgrade = True
    quick_connect_widget = QuickConnectWidget(controller=controller_mock)

    quick_connect_widget.connection_status_update(connection_state)

    assert quick_connect_widget.change_server_button.get_sensitive() \
        is change_server_button_sensitive


def test_quick_connect_widget_keeps_change_server_button_visible_throughout_a_server_change():
    controller_mock = Mock()
    controller_mock.server_selection_requires_upgrade = True
    quick_connect_widget = QuickConnectWidget(controller=controller_mock)
    sequence = [
        Connected(),
        Disconnecting(),
        Disconnected(StateContext(reconnection=Mock())),
        Connecting(),
        Connected(),
    ]

    for connection_state in sequence:
        quick_connect_widget.connection_status_update(connection_state)
        assert quick_connect_widget.change_server_revealer.get_reveal_child() is True


def test_quick_connect_widget_changes_server_when_change_server_button_is_clicked():
    controller_mock = Mock()
    controller_mock.server_selection_requires_upgrade = True
    quick_connect_widget = QuickConnectWidget(controller=controller_mock)

    quick_connect_widget.change_server_button.emit("clicked")
    process_gtk_events()

    controller_mock.change_server.assert_called_once()


SHORT_DELAY = 90
LONG_DELAY = 1200
ATTEMPT_LIMIT = 4


class FakeClock:
    """A clock that only moves when the test tells it to."""

    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now

    def advance(self, seconds):
        """Moves the clock forward."""
        self.now += seconds


def _cooldown_widget(requires_upgrade=True):
    """A widget whose controller reports a cooldown configuration, plus its clock."""
    controller_mock = Mock()
    controller_mock.server_selection_requires_upgrade = requires_upgrade
    controller_mock.client_config.change_server_attempt_limit = ATTEMPT_LIMIT
    controller_mock.client_config.change_server_short_delay_sec = SHORT_DELAY
    controller_mock.client_config.change_server_long_delay_sec = LONG_DELAY
    clock = FakeClock()
    widget = QuickConnectWidget(controller=controller_mock, clock=clock)
    return widget, clock, controller_mock


def _change_server(widget, times=1):
    """Goes through as many complete server changes as requested."""
    for _ in range(times):
        widget.change_server_button.emit("clicked")
        process_gtk_events()
        widget.connection_status_update(Connected())


def test_quick_connect_widget_disables_change_server_button_once_a_server_change_completes():
    widget, _, _ = _cooldown_widget()
    widget.connection_status_update(Connected())
    assert widget.change_server_button.get_sensitive() is True

    _change_server(widget)

    assert widget.change_server_button.get_sensitive() is False


def test_quick_connect_widget_shows_the_cooldown_card_while_the_cooldown_runs():
    widget, _, _ = _cooldown_widget()

    _change_server(widget)

    assert widget.cooldown_card_revealer.get_reveal_child() is True


def test_quick_connect_widget_counts_the_cooldown_down_on_the_change_server_button():
    widget, clock, _ = _cooldown_widget()
    _change_server(widget)
    assert widget.change_server_countdown_label.get_label() == "01:30"

    clock.advance(31)
    widget.connection_status_update(Connected())

    assert widget.change_server_countdown_label.get_label() == "00:59"
    assert widget.change_server_countdown_label.get_visible() is True


def test_quick_connect_widget_enables_change_server_button_again_once_the_cooldown_is_over():
    widget, clock, _ = _cooldown_widget()
    _change_server(widget)

    clock.advance(SHORT_DELAY)
    widget.connection_status_update(Connected())

    assert widget.change_server_button.get_sensitive() is True
    assert widget.cooldown_card_revealer.get_reveal_child() is False
    assert widget.change_server_countdown_label.get_visible() is False


def test_quick_connect_widget_hides_the_limit_reached_message_during_a_short_cooldown():
    widget, _, _ = _cooldown_widget()

    _change_server(widget)

    assert widget.cooldown_limit_reached_label.get_visible() is False


def test_quick_connect_widget_shows_the_limit_reached_message_once_the_attempt_limit_is_reached():
    widget, clock, _ = _cooldown_widget()

    for _ in range(ATTEMPT_LIMIT - 1):
        _change_server(widget)
        clock.advance(SHORT_DELAY)
    _change_server(widget)

    assert widget.cooldown_limit_reached_label.get_visible() is True
    assert widget.change_server_countdown_label.get_label() == "20:00"


def test_quick_connect_widget_does_not_start_a_cooldown_when_connecting_without_a_server_change():
    widget, _, _ = _cooldown_widget()

    widget.connection_status_update(Connected())

    assert widget.change_server_button.get_sensitive() is True
    assert widget.cooldown_card_revealer.get_reveal_child() is False


def test_quick_connect_widget_does_not_start_a_cooldown_when_the_server_change_fails():
    widget, _, _ = _cooldown_widget()

    widget.change_server_button.emit("clicked")
    process_gtk_events()
    widget.connection_status_update(Error())
    widget.connection_status_update(Connected())

    assert widget.change_server_button.get_sensitive() is True
    assert widget.cooldown_card_revealer.get_reveal_child() is False


def test_quick_connect_widget_does_not_start_a_cooldown_when_the_user_disconnects_instead():
    widget, _, _ = _cooldown_widget()

    widget.change_server_button.emit("clicked")
    process_gtk_events()
    widget.connection_status_update(Disconnected())
    widget.connection_status_update(Connected())

    assert widget.change_server_button.get_sensitive() is True
    assert widget.cooldown_card_revealer.get_reveal_child() is False


def test_quick_connect_widget_hides_the_cooldown_card_while_disconnected():
    widget, _, _ = _cooldown_widget()
    _change_server(widget)

    widget.connection_status_update(Disconnected())

    assert widget.cooldown_card_revealer.get_reveal_child() is False


def test_quick_connect_widget_keeps_the_cooldown_running_while_disconnected():
    widget, clock, _ = _cooldown_widget()
    _change_server(widget)

    widget.connection_status_update(Disconnected())
    clock.advance(30)
    widget.connection_status_update(Connected())

    assert widget.change_server_button.get_sensitive() is False
    assert widget.cooldown_card_revealer.get_reveal_child() is True
    assert widget.change_server_countdown_label.get_label() == "01:00"


def test_quick_connect_widget_is_not_kept_alive_by_a_running_cooldown_timer():
    """A timer holding on to the widget would stop it from ever being disposed,
    which is what cancels the timer.
    """
    widget, _, _ = _cooldown_widget()
    _change_server(widget)
    widget_ref = weakref.ref(widget)

    del widget
    gc.collect()

    assert widget_ref() is None


def test_quick_connect_widget_never_shows_a_cooldown_when_upgrade_is_not_required():
    widget, _, _ = _cooldown_widget(requires_upgrade=False)

    _change_server(widget)

    # Neither the change server button nor the cooldown card are shown to paying users
    assert widget.change_server_revealer.get_reveal_child() is False
    assert widget.cooldown_card_revealer.get_reveal_child() is False
