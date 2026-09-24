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
from proton.vpn.app.gtk.utils import accessibility
from proton.vpn.app.gtk.widgets.vpn.quick_connect_widget import QuickConnectWidget
from proton.vpn.connection.states import \
    Disconnected, \
    Connected, \
    Connecting, \
    Disconnecting, \
    Error, \
    StateContext

from tests.unit.testing_utils import process_gtk_events, run_main_loop


@pytest.mark.parametrize("connection_state, expected_label", [
    (Disconnected(), "Connect"),
    (Connecting(), "Cancel Connection"),
    (Connected(), "Disconnect"),
    (Error(), "Cancel Connection"),
])
def test_quick_connect_widget_relabels_the_action_button_for_the_connection_state(
        connection_state, expected_label
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
            assert quick_connect_widget.action_button.get_visible() is True
            assert quick_connect_widget.action_button.get_label() == expected_label
        finally:
            main_loop.quit()

    GLib.idle_add(run)
    run_main_loop(main_loop)


@pytest.mark.parametrize("connection_state", [Connecting(), Connected(), Error()])
def test_the_action_button_keeps_focus_across_state_changes(connection_state):
    """One relabelling button rather than two swapped in and out: nothing is
    hidden, so focus never falls back to the search entry and no focus change
    interrupts speech in progress.
    """
    widget = QuickConnectWidget(controller=Mock())
    window = Gtk.Window()
    window.set_child(widget)
    main_loop = GLib.MainLoop()

    def run():
        window.present()
        widget.connection_status_update(Disconnected())
        widget.action_button.grab_focus()

        try:
            assert widget.action_button.is_focus() is True

            widget.connection_status_update(connection_state)

            assert widget.action_button.is_focus() is True
        finally:
            main_loop.quit()

    GLib.idle_add(run)
    run_main_loop(main_loop)


def test_a_state_change_does_not_pull_focus_onto_the_action_button():
    widget = QuickConnectWidget(controller=Mock())
    window = Gtk.Window()
    window.set_child(widget)
    main_loop = GLib.MainLoop()

    def run():
        window.present()
        widget.connection_status_update(Disconnected())

        try:
            widget.connection_status_update(Connecting())

            assert widget.action_button.is_focus() is False
        finally:
            main_loop.quit()

    GLib.idle_add(run)
    run_main_loop(main_loop)


def test_set_accessible_details_skips_the_button_while_it_holds_focus():
    """A screen reader speaks a description change on the focused object,
    which would read the detail out over the announcement.
    """
    widget = QuickConnectWidget(controller=Mock())
    widget.action_button = Mock()
    widget.action_button.has_focus.return_value = True

    widget.set_accessible_details("Switzerland, Zurich - CH#1")

    widget.action_button.update_property.assert_not_called()


def test_set_accessible_details_describes_the_button_when_it_is_unfocused():
    widget = QuickConnectWidget(controller=Mock())
    widget.action_button = Mock()
    widget.action_button.has_focus.return_value = False

    widget.set_accessible_details("Switzerland, Zurich - CH#1")

    widget.action_button.update_property.assert_called_once_with(
        [Gtk.AccessibleProperty.DESCRIPTION], ["Switzerland, Zurich - CH#1"]
    )


def test_the_same_detail_is_never_written_to_the_button_twice():
    """Rewriting the same text can still be read out: a screen reader that
    has not seen the description before has no previous value to compare it
    against.
    """
    widget = QuickConnectWidget(controller=Mock())
    widget.action_button = Mock()
    widget.action_button.has_focus.return_value = False

    widget.set_accessible_details("Fastest free server")
    widget.set_accessible_details("Fastest free server")

    widget.action_button.update_property.assert_called_once_with(
        [Gtk.AccessibleProperty.DESCRIPTION], ["Fastest free server"]
    )


def test_quick_connect_widget_connects_to_fastest_server_when_the_action_button_is_clicked():
    controller_mock = Mock()
    quick_connect_widget = QuickConnectWidget(controller=controller_mock)
    quick_connect_widget.connection_status_update(Disconnected())

    quick_connect_widget.action_button.emit("clicked")
    process_gtk_events()

    controller_mock.connect_to_fastest_server.assert_called_once()


def test_quick_connect_widget_disconnects_when_the_action_button_is_clicked_while_connected():
    controller_mock = Mock()
    quick_connect_widget = QuickConnectWidget(controller=controller_mock)
    quick_connect_widget.connection_status_update(Connected())

    quick_connect_widget.action_button.emit("clicked")
    process_gtk_events()

    controller_mock.disconnect.assert_called_once()


@pytest.mark.parametrize("connection_state, change_server_button_visible", [
    (Disconnected(), False),
    (Connecting(), False),
    (Connected(), True),
    (Error(), False),
])
def test_quick_connect_widget_shows_change_server_button_only_once_connected(
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


def test_quick_connect_widget_hides_change_server_button_during_a_reconnect_started_elsewhere():
    controller_mock = Mock()
    controller_mock.server_selection_requires_upgrade = True
    # A normal, user-initiated reconnect, not an automatic retry.
    controller_mock.reconnector.is_recovering_connection = False
    quick_connect_widget = QuickConnectWidget(controller=controller_mock)
    sequence = [
        (Connected(), True),
        (Disconnecting(), False),
        (Disconnected(StateContext(reconnection=Mock())), False),
        (Connecting(), False),
        (Connected(), True),
    ]

    for connection_state, expected_visible in sequence:
        quick_connect_widget.connection_status_update(connection_state)
        assert quick_connect_widget.change_server_revealer.get_reveal_child() is expected_visible


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


class FakeScheduler:
    """Stands in for GLib.timeout_add_seconds/source_remove: only fires when told to."""

    def __init__(self):
        self._next_id = 1
        self._pending = {}

    def schedule(self, delay_seconds, callback):
        """Records a scheduled timeout."""
        src_id = self._next_id
        self._next_id += 1
        self._pending[src_id] = (delay_seconds, callback)
        return src_id

    def cancel(self, src_id):
        """Drops a scheduled timeout."""
        self._pending.pop(src_id, None)

    @property
    def pending_count(self):
        """How many timeouts are scheduled."""
        return len(self._pending)

    @property
    def pending_delay(self):
        """The delay the sole pending timeout was scheduled with."""
        assert len(self._pending) == 1
        return next(iter(self._pending.values()))[0]

    def fire(self):
        """Fires the sole pending timeout, as if its delay had elapsed."""
        assert len(self._pending) == 1
        src_id, (_, callback) = next(iter(self._pending.items()))
        del self._pending[src_id]
        callback()


def _slow_connection_widget(requires_upgrade=True, announce=None):
    """A widget with a fake scheduler standing in for the slow-connection timer."""
    controller_mock = Mock()
    controller_mock.server_selection_requires_upgrade = requires_upgrade
    controller_mock.client_config.change_server_attempt_limit = ATTEMPT_LIMIT
    controller_mock.client_config.change_server_short_delay_sec = SHORT_DELAY
    controller_mock.client_config.change_server_long_delay_sec = LONG_DELAY
    # No automatic reconnection in progress by default: tests that need one set this True.
    controller_mock.reconnector.is_recovering_connection = False
    scheduler = FakeScheduler()
    clock = FakeClock()
    widget = QuickConnectWidget(
        controller=controller_mock,
        clock=clock,
        schedule_timeout=scheduler.schedule,
        cancel_timeout=scheduler.cancel,
        announce=announce or accessibility.announce,
    )
    return widget, scheduler, controller_mock, clock


def test_the_slow_connection_unlock_is_announced():
    """The button appears on a timer, so nothing else tells a screen reader
    it is there.
    """
    announced = []
    widget, scheduler, *_ = _slow_connection_widget(
        announce=lambda _widget, message: announced.append(message)
    )
    widget.connection_status_update(Connecting())
    assert announced == []

    scheduler.fire()

    assert announced == [QuickConnectWidget.CHANGE_SERVER_AVAILABLE_MESSAGE]


def test_the_slow_connection_unlock_is_announced_once_across_retries():
    """Error and Connecting cycle without clearing the unlock, so the button
    stays usable and must not be announced on every retry.
    """
    announced = []
    widget, scheduler, *_ = _slow_connection_widget(
        announce=lambda _widget, message: announced.append(message)
    )
    widget.connection_status_update(Connecting())
    scheduler.fire()
    assert announced == [QuickConnectWidget.CHANGE_SERVER_AVAILABLE_MESSAGE]

    widget.connection_status_update(Error())
    widget.connection_status_update(Connecting())
    scheduler.fire()

    assert announced == [QuickConnectWidget.CHANGE_SERVER_AVAILABLE_MESSAGE]


def test_connecting_does_not_announce_change_server_availability():
    """Only a slow-connection unlock or a cooldown ending announces it."""
    announced = []
    widget, *_ = _slow_connection_widget(
        announce=lambda _widget, message: announced.append(message)
    )

    widget.connection_status_update(Connected())

    assert announced == []


def test_quick_connect_widget_unlocks_change_server_once_connecting_takes_too_long():
    widget, scheduler, *_ = _slow_connection_widget()

    widget.connection_status_update(Connecting())
    assert widget.change_server_button.get_sensitive() is False
    assert scheduler.pending_delay == QuickConnectWidget.SLOW_CONNECTION_TIMEOUT_SECONDS

    scheduler.fire()

    assert widget.change_server_button.get_sensitive() is True


def test_quick_connect_widget_slow_connection_unlock_bypasses_an_active_cooldown():
    widget, scheduler, *_ = _slow_connection_widget()
    _change_server(widget)  # Arms a cooldown.
    assert widget.change_server_button.get_sensitive() is False
    assert widget.cooldown_card_revealer.get_reveal_child() is True

    widget.connection_status_update(Connecting())
    scheduler.fire()

    assert widget.change_server_button.get_sensitive() is True
    assert widget.cooldown_card_revealer.get_reveal_child() is False
    assert widget.change_server_countdown_label.get_visible() is False


def test_quick_connect_widget_brings_back_an_active_cooldown_after_a_slow_connection_unlock():
    """Changing server via the slow-connection unlock doesn't cancel a pre-existing
    cooldown, only hides it: once connected, it must resume.
    """
    widget, scheduler, *_ = _slow_connection_widget()
    _change_server(widget)  # Arms a SHORT_DELAY (90s) cooldown.

    widget.connection_status_update(Connecting())
    scheduler.fire()
    widget.change_server_button.emit("clicked")
    process_gtk_events()
    widget.connection_status_update(Disconnecting(StateContext(reconnection=Mock())))
    widget.connection_status_update(Disconnected(StateContext(reconnection=Mock())))
    widget.connection_status_update(Connecting())
    widget.connection_status_update(Connected())

    # No time has passed on the fake clock: the original cooldown is untouched.
    assert widget.change_server_button.get_sensitive() is False
    assert widget.cooldown_card_revealer.get_reveal_child() is True
    assert widget.change_server_countdown_label.get_label() == "01:30"


def test_quick_connect_widget_reapplies_the_cooldown_after_a_slow_attempt_connects_unassisted():
    """Waiting out a slow attempt instead of clicking Change Server resumes an active cooldown
    if connection succeeds.
    """
    widget, scheduler, *_ = _slow_connection_widget()
    _change_server(widget)  # Arms a SHORT_DELAY (90s) cooldown.

    widget.connection_status_update(Connecting())
    scheduler.fire()
    assert widget.change_server_button.get_sensitive() is True
    assert widget.cooldown_card_revealer.get_reveal_child() is False

    widget.connection_status_update(Connected())

    # No time has passed on the fake clock: the original cooldown is untouched.
    assert widget.change_server_button.get_sensitive() is False
    assert widget.cooldown_card_revealer.get_reveal_child() is True
    assert widget.change_server_countdown_label.get_label() == "01:30"


def test_quick_connect_widget_does_not_reapply_an_expired_cooldown_unassisted():
    widget, scheduler, _, clock = _slow_connection_widget()
    _change_server(widget)  # Arms a SHORT_DELAY (90s) cooldown.

    widget.connection_status_update(Connecting())
    scheduler.fire()
    clock.advance(SHORT_DELAY)  # The cooldown genuinely expires while we wait.
    widget.connection_status_update(Connected())

    assert widget.change_server_button.get_sensitive() is True
    assert widget.cooldown_card_revealer.get_reveal_child() is False


def test_quick_connect_widget_cancels_slow_connection_timer_while_disconnecting():
    widget, scheduler, *_ = _slow_connection_widget()

    widget.connection_status_update(Connecting())
    widget.connection_status_update(Disconnecting())

    assert scheduler.pending_count == 0


def test_quick_connect_widget_cancels_slow_connection_timer_on_a_direct_disconnect():
    """Disconnected() can follow Connecting() directly, skipping Disconnecting(),
    when something external tears down the VPN mid-attempt. That must
    cancel a pending or already-fired timer too, not just the Disconnecting path.
    """
    widget, scheduler, *_ = _slow_connection_widget()

    widget.connection_status_update(Connecting())
    scheduler.fire()
    assert widget.change_server_button.get_sensitive() is True

    widget.connection_status_update(Disconnected())  # No Disconnecting() first.

    assert widget.change_server_button.get_sensitive() is False

    # A fresh attempt requires a new 8-second wait: nothing was left over.
    widget.connection_status_update(Connecting())
    assert widget.change_server_button.get_sensitive() is False
    assert scheduler.pending_count == 1


def test_quick_connect_widget_keeps_slow_connection_unlock_through_an_automatic_reconnect():
    """Disconnecting() with a queued reconnection is teardown for an automatic retry,
    not a manual cancellation, so the unlock triggered by a slow attempt must persist.
    """
    widget, scheduler, controller_mock, _ = _slow_connection_widget()

    widget.connection_status_update(Connecting())
    scheduler.fire()
    widget.connection_status_update(Error())
    controller_mock.reconnector.is_recovering_connection = True
    widget.connection_status_update(Disconnecting(StateContext(reconnection=Mock())))
    widget.connection_status_update(Disconnected(StateContext(reconnection=Mock())))
    widget.connection_status_update(Connecting())

    assert widget.change_server_button.get_sensitive() is True


def test_quick_connect_widget_a_change_server_click_overrides_a_concurrent_automatic_retry():
    """A click resets the unlock and waits its own 8 seconds, retry or not."""
    widget, scheduler, controller_mock, _ = _slow_connection_widget()
    controller_mock.reconnector.is_recovering_connection = True

    widget.connection_status_update(Connecting())
    scheduler.fire()
    assert widget.change_server_button.get_sensitive() is True

    widget.change_server_button.emit("clicked")
    process_gtk_events()
    widget.connection_status_update(Disconnecting(StateContext(reconnection=Mock())))
    widget.connection_status_update(Disconnected(StateContext(reconnection=Mock())))
    widget.connection_status_update(Connecting())

    assert widget.change_server_button.get_sensitive() is False
    assert widget.change_server_revealer.get_reveal_child() is False


def test_quick_connect_widget_requires_a_fresh_slow_connection_unlock_for_the_next_attempt():
    """The unlock has to be earned again by the attempt it just started."""
    widget, scheduler, *_ = _slow_connection_widget()

    widget.connection_status_update(Connecting())
    scheduler.fire()
    assert widget.change_server_revealer.get_reveal_child() is True

    widget.change_server_button.emit("clicked")
    process_gtk_events()
    widget.connection_status_update(Disconnecting(StateContext(reconnection=Mock())))
    assert widget.change_server_revealer.get_reveal_child() is False

    widget.connection_status_update(Disconnected(StateContext(reconnection=Mock())))
    widget.connection_status_update(Connecting())
    assert widget.change_server_revealer.get_reveal_child() is False

    scheduler.fire()
    assert widget.change_server_revealer.get_reveal_child() is True


def test_quick_connect_widget_hides_the_countdown_label_when_the_slow_connection_unlock_hides():
    """The countdown label sits inside the button itself, so it must not flash back
    on while the button's own revealer is still mid-animation collapsing it away.
    """
    widget, scheduler, *_ = _slow_connection_widget()
    _change_server(widget)  # Arms a cooldown.

    widget.connection_status_update(Connecting())
    scheduler.fire()
    widget.change_server_button.emit("clicked")
    process_gtk_events()
    widget.connection_status_update(Disconnecting(StateContext(reconnection=Mock())))

    assert widget.change_server_revealer.get_reveal_child() is False
    assert widget.change_server_countdown_label.get_visible() is False


def test_quick_connect_widget_does_not_count_a_slow_connection_unlock_towards_the_limit():
    widget, scheduler, *_ = _slow_connection_widget()

    widget.connection_status_update(Connecting())
    scheduler.fire()
    widget.change_server_button.emit("clicked")
    process_gtk_events()
    widget.connection_status_update(Disconnecting(StateContext(reconnection=Mock())))
    widget.connection_status_update(Disconnected(StateContext(reconnection=Mock())))
    widget.connection_status_update(Connecting())
    widget.connection_status_update(Connected())

    assert widget.cooldown_card_revealer.get_reveal_child() is False
    assert widget.change_server_button.get_sensitive() is True


def test_quick_connect_widget_keeps_change_server_visible_when_slow_connection_unlocked_on_error():
    """Once unlocked, the button must stay visible through an Error to stay visible
    through automatic retries.
    """
    widget, scheduler, *_ = _slow_connection_widget()

    widget.connection_status_update(Connecting())
    scheduler.fire()
    widget.connection_status_update(Error())

    assert widget.change_server_revealer.get_reveal_child() is True


def test_quick_connect_widget_hides_change_server_on_error_without_a_slow_connection_unlock():
    widget, *_ = _slow_connection_widget()

    widget.connection_status_update(Connecting())
    widget.connection_status_update(Error())  # no timer fired yet: not unlocked

    assert widget.change_server_revealer.get_reveal_child() is False


def test_quick_connect_widget_hides_change_server_on_error_after_a_successful_connection():
    widget, *_ = _slow_connection_widget()

    widget.connection_status_update(Connected())
    assert widget.change_server_revealer.get_reveal_child() is True

    widget.connection_status_update(Error())

    assert widget.change_server_revealer.get_reveal_child() is False


def test_quick_connect_widget_reveals_change_server_on_slow_connection_unlock_while_on_error():
    """The timer can fire while Error is displayed, not just Connecting."""
    widget, scheduler, *_ = _slow_connection_widget()

    widget.connection_status_update(Connecting())
    widget.connection_status_update(Error())
    assert widget.change_server_revealer.get_reveal_child() is False

    scheduler.fire()

    assert widget.change_server_revealer.get_reveal_child() is True
    assert widget.change_server_button.get_sensitive() is True


def test_quick_connect_widget_cancels_slow_connection_timer_and_unlock_once_connected():
    widget, scheduler, *_ = _slow_connection_widget()

    widget.connection_status_update(Connecting())
    scheduler.fire()
    widget.connection_status_update(Connected())

    assert scheduler.pending_count == 0

    # A fresh attempt requires a new 8-second wait: the unlock was reset.
    widget.connection_status_update(Disconnected())
    widget.connection_status_update(Connecting())
    assert widget.change_server_button.get_sensitive() is False
    assert scheduler.pending_count == 1


def test_quick_connect_widget_cancels_the_old_timer_before_a_new_attempt_starts():
    """A stale timer would unlock the button during a later, unrelated attempt."""
    widget, scheduler, *_ = _slow_connection_widget()

    widget.connection_status_update(Connecting())  # attempt 1, resolves quickly
    widget.connection_status_update(Connected())
    widget.connection_status_update(Disconnected())
    widget.connection_status_update(Connecting())  # attempt 2

    assert scheduler.pending_count == 1  # only attempt 2's timer is still armed


def test_quick_connect_widget_never_starts_slow_connection_timer_when_upgrade_is_not_required():
    widget, scheduler, *_ = _slow_connection_widget(requires_upgrade=False)

    widget.connection_status_update(Connecting())

    assert scheduler.pending_count == 0


def test_quick_connect_widget_is_not_kept_alive_by_a_pending_slow_connection_timer():
    widget, *_ = _slow_connection_widget()
    widget.connection_status_update(Connecting())
    widget_ref = weakref.ref(widget)

    del widget
    gc.collect()

    assert widget_ref() is None
