"""
This module defines the Quick Connect widget.


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
from typing import Callable, Optional

from gi.repository import GLib
from proton.vpn.connection import states

from proton.vpn.app.gtk import Gtk
from proton.vpn.app.gtk.controller import Controller
from proton.vpn.app.gtk.translator import C_
from proton.vpn.app.gtk.utils.safe_signal_connect import safe_signal_connect
from proton.vpn.app.gtk.utils.change_server_cooldown import \
    ChangeServerCooldown, \
    format_countdown
from proton.vpn.app.gtk.utils.glib import weak_deferred_glib_callback
from proton.vpn import logging

logger = logging.getLogger(__name__)


class QuickConnectWidget(Gtk.Box):  # pylint: disable=too-many-instance-attributes
    """Widget handling the "Quick Connect" functionality."""
    CHANGE_SERVER_LABEL = C_("button", "Change server")
    LIMIT_REACHED_LABEL = C_(
        "label", "You've reached the maximum number of free server changes for now"
    )
    UPGRADE_LABEL = C_("label", "Get unlimited server changes with VPN Plus.")
    COOLDOWN_TICK_INTERVAL_SECONDS = 1
    SLOW_CONNECTION_TIMEOUT_SECONDS = 8

    def __init__(
            self,
            controller: Controller,
            clock: Optional[Callable[[], float]] = None,
            schedule_timeout: Callable[[int, Callable[[], bool]], int] = GLib.timeout_add_seconds,
            cancel_timeout: Callable[[int], None] = GLib.source_remove,
    ):
        super().__init__(spacing=10)
        self.set_name("quick-connect-widget")
        self._controller = controller
        self._connection_state: states.State = None
        # Whether the "Change server" button is ever shown for this user.
        self._show_change_server = controller.server_selection_requires_upgrade
        self._cooldown = ChangeServerCooldown(clock) if clock else ChangeServerCooldown()
        self._cooldown_tick_src_id: Optional[int] = None
        # Whether a cooldown is pending once a "Change server" requested
        # connection has been established
        self._cooldown_pending = False
        self._schedule_timeout = schedule_timeout
        self._cancel_timeout = cancel_timeout
        self._slow_connection_timer_src_id: Optional[int] = None
        # Whether the current connection attempt has taken long enough to
        # unlock "Change server" regardless of it being on cooldown.
        self._change_server_unlocked_by_slow_connection = False
        # Whether a "Change server" action is in progress
        self._change_server_requested = False

        self.set_orientation(Gtk.Orientation.VERTICAL)
        self.connect_button = Gtk.Button(label=C_("button", "Connect"))
        self.connect_button.add_css_class("primary")
        safe_signal_connect(
            self.connect_button,
            "clicked", self._on_connect_button_clicked)
        self.connect_button.set_visible(False)
        self.append(self.connect_button)
        self.disconnect_button = Gtk.Button(label=C_("button", "Disconnect"))
        self.disconnect_button.add_css_class("danger")
        safe_signal_connect(
            self.disconnect_button,
            "clicked", self._on_disconnect_button_clicked)
        self.disconnect_button.set_visible(False)
        self.append(self.disconnect_button)
        self.change_server_button = Gtk.Button()
        self.change_server_button.add_css_class("secondary")
        self.change_server_button.set_child(self._build_change_server_button_child())
        safe_signal_connect(
            self.change_server_button,
            "clicked",
            self._on_change_server_button_clicked
        )
        self.change_server_button.set_sensitive(False)
        self.change_server_revealer = Gtk.Revealer()
        self.change_server_revealer.set_child(self.change_server_button)
        # Appended last so it renders below whichever of the connect/disconnect
        # buttons is showing: Gtk.Box skips hidden children, so the hidden one
        # costs neither height nor spacing.
        self.append(self.change_server_revealer)
        self.cooldown_card_revealer = Gtk.Revealer()
        self.cooldown_card_revealer.set_child(self._build_cooldown_card())
        self.append(self.cooldown_card_revealer)

    def _build_change_server_button_child(self) -> Gtk.Widget:
        """Builds the button content: the label, plus the cooldown countdown.

        The countdown is a separate label so that it can stay legible while
        the rest of the button is dimmed by its insensitive state.
        """
        box = Gtk.Box(spacing=8)
        box.set_halign(Gtk.Align.CENTER)
        box.append(Gtk.Label(label=QuickConnectWidget.CHANGE_SERVER_LABEL))
        self.change_server_countdown_label = Gtk.Label()
        self.change_server_countdown_label.add_css_class("change-server-countdown")
        self.change_server_countdown_label.set_visible(False)
        box.append(self.change_server_countdown_label)
        return box

    def _build_cooldown_card(self) -> Gtk.Widget:
        """Builds the card shown below the button while a cooldown is running.

        The upgrade prompt shows for the whole cooldown. The limit reached
        message only applies to the long one, so it starts hidden and is
        toggled by _refresh_change_server().
        """
        self.cooldown_limit_reached_label = self._build_cooldown_card_label(
            QuickConnectWidget.LIMIT_REACHED_LABEL, css_class="heading"
        )
        self.cooldown_limit_reached_label.set_visible(False)
        self.cooldown_upgrade_label = self._build_cooldown_card_label(
            QuickConnectWidget.UPGRADE_LABEL, css_class="dim-label"
        )

        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        card.set_name("change-server-cooldown-card")
        card.append(self.cooldown_limit_reached_label)
        card.append(self.cooldown_upgrade_label)
        return card

    @staticmethod
    def _build_cooldown_card_label(text: str, css_class: str) -> Gtk.Label:
        """Builds a left aligned, wrapping label for the cooldown card."""
        label = Gtk.Label(label=text)
        label.add_css_class(css_class)
        label.set_halign(Gtk.Align.START)
        label.set_xalign(0)
        label.set_wrap(True)
        label.set_max_width_chars(35)
        return label

    @property
    def connection_state(self):
        """Returns the current connection state."""
        return self._connection_state

    @connection_state.setter
    def connection_state(self, connection_state: states.State):
        """Sets the current connection state, updating the UI accordingly."""
        # pylint: disable=duplicate-code
        self._connection_state = connection_state

        # Update the UI according to the connection state.
        if isinstance(connection_state, states.Disconnected) \
                and not connection_state.context.reconnection:
            self._on_connection_state_disconnected()
        elif isinstance(connection_state, states.Connecting):
            self._on_connection_state_connecting()
        elif isinstance(connection_state, states.Connected):
            self._on_connection_state_connected()
        elif isinstance(connection_state, states.Error):
            self._on_connection_state_error()
        elif isinstance(connection_state, states.Disconnecting):
            self._on_connection_state_disconnecting()

        self._refresh_change_server()

    def connection_status_update(self, connection_state):
        """This method is called by VPNWidget whenever the VPN connection status changes."""
        self.connection_state = connection_state

    def _on_connection_state_disconnected(self):
        self.disconnect_button.set_visible(False)
        self.connect_button.set_visible(True)
        self.change_server_revealer.set_reveal_child(False)
        # The server change did not complete, so it does not count.
        self._cooldown_pending = False
        self._change_server_requested = False
        self._cancel_slow_connection_timer()
        self._change_server_unlocked_by_slow_connection = False

    def _on_connection_state_connecting(self):
        self.connect_button.set_visible(False)
        self.disconnect_button.set_label(C_("button", "Cancel Connection"))
        self.disconnect_button.set_visible(True)
        if self._show_change_server and not self._slow_connection_timer_is_running:
            self._start_slow_connection_timer()

    def _on_connection_state_connected(self):
        self.connect_button.set_visible(False)
        self.disconnect_button.set_label(C_("button", "Disconnect"))
        self.disconnect_button.set_visible(True)
        self.change_server_revealer.set_reveal_child(self._show_change_server)
        self._cancel_slow_connection_timer()
        self._change_server_unlocked_by_slow_connection = False
        self._change_server_requested = False
        if self._cooldown_pending:
            self._cooldown_pending = False
            self._start_cooldown()

    def _on_connection_state_error(self):
        self.connect_button.set_visible(False)
        self.disconnect_button.set_label(C_("button", "Cancel Connection"))
        self.disconnect_button.set_visible(True)
        if not self._change_server_unlocked_by_slow_connection:
            self.change_server_revealer.set_reveal_child(False)
        # The server change did not complete, so it does not count.
        self._cooldown_pending = False
        self._change_server_requested = False

    def _on_connection_state_disconnecting(self):
        is_automatic_retry = (
            self._controller.reconnector.is_recovering_connection
            and not self._change_server_requested
        )
        if is_automatic_retry:
            # Automatic retry: leave change server button in current state
            return

        # Only a click on the (normal, not slow-connection-unlocked) change server
        # button keeps the UI visible through the reconnect - anything else (a
        # reconnect started elsewhere, or changing server via the slow-connection
        # unlock) hides it.
        keep_change_server_visible = (
            self._change_server_requested and not self._change_server_unlocked_by_slow_connection
        )
        if not keep_change_server_visible:
            self.change_server_revealer.set_reveal_child(False)
        self._change_server_requested = False
        self._cancel_slow_connection_timer()
        self._change_server_unlocked_by_slow_connection = False

    def _on_connect_button_clicked(self, _):
        logger.info("Connect to fastest server", category="ui.tray", event="connect")
        future = self._controller.connect_to_fastest_server()
        future.add_done_callback(lambda f: GLib.idle_add(f.result))  # bubble up exceptions if any.

    def _on_disconnect_button_clicked(self, _):
        logger.info("Disconnect from VPN", category="ui", event="disconnect")
        future = self._controller.disconnect()
        future.add_done_callback(lambda f: GLib.idle_add(f.result))  # bubble up exceptions if any.

    def _on_change_server_button_clicked(self, _):
        logger.info("Change to another server", category="ui", event="change_server")
        self._change_server_requested = True
        # Changing server via the slow-connection unlock doesn't count towards the cooldown limit.
        self._cooldown_pending = not self._change_server_unlocked_by_slow_connection
        future = self._controller.change_server()
        future.add_done_callback(lambda f: GLib.idle_add(f.result))  # bubble up exceptions if any.

    def _start_cooldown(self):
        """Starts a cooldown and the timer refreshing the countdown."""
        self._cooldown.arm(self._controller.client_config)
        self._cancel_cooldown_tick()
        self._cooldown_tick_src_id = GLib.timeout_add_seconds(
            QuickConnectWidget.COOLDOWN_TICK_INTERVAL_SECONDS,
            weak_deferred_glib_callback(self._on_cooldown_tick)
        )

    def _on_cooldown_tick(self) -> bool:
        self._refresh_change_server()

        if self._cooldown.is_active:
            return GLib.SOURCE_CONTINUE

        self._cooldown_tick_src_id = None
        return GLib.SOURCE_REMOVE

    def _cancel_cooldown_tick(self):
        if self._cooldown_tick_src_id:
            GLib.source_remove(self._cooldown_tick_src_id)
            self._cooldown_tick_src_id = None

    @property
    def _slow_connection_timer_is_running(self):
        """Returns True if the slow-connection timer is currently scheduled."""
        return self._slow_connection_timer_src_id is not None

    def _start_slow_connection_timer(self):
        """Unlocks "Change server" once a connection attempt is taking too long."""
        self._slow_connection_timer_src_id = self._schedule_timeout(
            QuickConnectWidget.SLOW_CONNECTION_TIMEOUT_SECONDS,
            weak_deferred_glib_callback(self._on_slow_connection_timeout, one_shot=True)
        )

    def _on_slow_connection_timeout(self):
        self._slow_connection_timer_src_id = None
        self._change_server_unlocked_by_slow_connection = True
        self.change_server_revealer.set_reveal_child(self._show_change_server)
        self._refresh_change_server()

    def _cancel_slow_connection_timer(self):
        if self._slow_connection_timer_src_id:
            self._cancel_timeout(self._slow_connection_timer_src_id)
            self._slow_connection_timer_src_id = None

    def _refresh_change_server(self):
        """Updates whether the server can be changed, and the cooldown display.
        """
        cooldown_is_active = self._cooldown.is_active
        is_connected = isinstance(self._connection_state, states.Connected)
        # Only an established connection can be changed away from, unless the
        # current attempt has taken long enough to unlock it regardless.
        self.change_server_button.set_sensitive(
            self._show_change_server
            and (
                (is_connected and not cooldown_is_active)
                or self._change_server_unlocked_by_slow_connection
            )
        )

        change_server_is_shown = self.change_server_revealer.get_reveal_child()
        # A slow-connection unlock bypasses the cooldown but doesn't cancel it, so
        # hide its display while unlocked. It reappears on its own once the unlock is gone, if
        # still active.
        show_cooldown = cooldown_is_active and not self._change_server_unlocked_by_slow_connection
        self.cooldown_card_revealer.set_reveal_child(show_cooldown and change_server_is_shown)
        self.cooldown_limit_reached_label.set_visible(self._cooldown.is_long)
        self.change_server_countdown_label.set_visible(show_cooldown and change_server_is_shown)
        self.change_server_countdown_label.set_label(
            format_countdown(self._cooldown.remaining_seconds)
        )
