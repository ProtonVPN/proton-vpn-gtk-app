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
from gi.repository import GLib
from proton.vpn.app.gtk import Gtk
from proton.vpn.connection import events, states
from proton.vpn.app.gtk.controller import Controller
from proton.vpn.app.gtk.widgets.main.loading_widget import OverlayWidget, LoadingConnectionWidget
from proton.vpn.app.gtk.widgets.main.notifications import Notifications
from proton.vpn.app.gtk.widgets.vpn.port_forward_widget import PortForwardRevealer
from proton.vpn.app.gtk.widgets.headerbar.menu.settings.split_tunneling.split_tunneling import \
    SPLIT_TUNNELING_TOGGLE_SETTING_NAME
from proton.vpn import logging

logger = logging.getLogger(__name__)

SPLIT_TUNNELING_APP_RESTART_MESSAGE = \
    "Split tunneling enabled. Remember to restart affected apps."


class VPNConnectionStatusWidget(Gtk.Box):
    """Displays the current connection status."""
    MAXIMUM_SESSIONS_ERROR = "You've reached your maximum device limit. " \
        "To reconnect to VPN, please disconnect from another device."

    def __init__(
        self, controller: Controller,
        overlay_widget: OverlayWidget,
        notifications: Notifications,
        port_forward_revealer: PortForwardRevealer = None
    ):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)

        self.set_name("vpn-connection-status-widget")
        self._overlay_widget = overlay_widget
        self._controller = controller
        self._notifications = notifications

        self._connection_status_label = Gtk.Label(label="")
        self._connection_status_label.set_name("connection-status-label")
        self._loading_widget = self._build_loading_connection_widget()

        self.append(self._connection_status_label)

        display_port_forwarding = controller.feature_flags\
            .get("DisplayPortForwarding")
        if display_port_forwarding:
            self._port_forward_revealer = port_forward_revealer \
                or PortForwardRevealer(notifications)
            self.append(self._port_forward_revealer)
        else:
            self._port_forward_revealer = None

    def _build_loading_connection_widget(self) -> LoadingConnectionWidget:
        cancel_button = Gtk.Button.new_with_label("Cancel Connection")
        cancel_button.connect("clicked", self._on_cancel_button_clicked)

        loading_widget = LoadingConnectionWidget(
            label="",
            cancel_button=cancel_button
        )

        return loading_widget

    def _on_cancel_button_clicked(self, _):
        logger.info("Disconnect from VPN", category="ui", event="disconnect")
        future = self._controller.disconnect()
        future.add_done_callback(lambda f: GLib.idle_add(f.result))

    @property
    def status_message(self) -> str:
        """Returns the connection status message being displayed to the user."""
        return self._connection_status_label.get_label()

    def connection_status_update(self, connection_state: states.State):
        """This method is called by VPNWidget whenever the VPN connection status changes."""
        self._update_connection_status_label(connection_state)

    def _update_connection_status_label(self, connection_state: states.State):
        connection = connection_state.context.connection

        label = ""
        if isinstance(connection_state, states.Disconnected):
            label = "You are disconnected"
            self._overlay_widget.hide()
        elif isinstance(connection_state, states.Connecting):
            self._loading_widget.set_label(f"Connecting to {connection.server_name}")
            self._overlay_widget.show(self._loading_widget)
        elif isinstance(connection_state, states.Connected):
            label = f"You are connected to {connection.server_name}"
            self._overlay_widget.hide()
            if self._split_tunneling_enabled:
                self._notifications.show_info_message(
                    message=SPLIT_TUNNELING_APP_RESTART_MESSAGE
                )
        elif isinstance(connection_state, states.Disconnecting):
            label = f"Disconnecting from {connection.server_name}"
        elif isinstance(connection_state, states.Error):
            last_connection_event = connection_state.context.event
            label = "Connection error"
            if isinstance(last_connection_event, events.TunnelSetupFailed):
                label = f"{label}: tunnel setup failed"
            elif isinstance(last_connection_event, events.AuthDenied):
                label = f"{label}: authentication denied"
            elif isinstance(last_connection_event, events.Timeout):
                label = f"{label}: timeout"
            elif isinstance(last_connection_event, events.DeviceDisconnected):
                label = f"{label}: device disconnected"
            elif isinstance(last_connection_event, events.MaximumSessionsReached):
                label = f"{label}: session limit reached"
                self._notifications.show_error_dialog(
                    message=self.MAXIMUM_SESSIONS_ERROR,
                    title=label
                )

            self._overlay_widget.hide()

        # This condition will be removed once we remove the feature flag.
        if self._port_forward_revealer:
            self._port_forward_revealer.on_new_state(connection_state)

        self._connection_status_label.set_label(label)

    @property
    def _split_tunneling_enabled(self) -> bool:
        """Check if split tunneling is enabled."""
        return self._controller.get_setting_attr(SPLIT_TUNNELING_TOGGLE_SETTING_NAME)
