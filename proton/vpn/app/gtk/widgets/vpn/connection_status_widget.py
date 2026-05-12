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
from pathlib import Path
from typing import Optional, cast
from gi.repository import Gdk, GdkPixbuf
from proton.vpn.app.gtk import Gtk
from proton.vpn.connection import events, states
from proton.vpn.app.gtk.assets import icons
from proton.vpn.app.gtk.controller import Controller
from proton.vpn.app.gtk.widgets.vpn.serverlist.icons import DoubleFlagIcon
from proton.vpn.session.servers import ServerFeatureEnum, TierEnum
from proton.vpn.app.gtk.widgets.main.notifications import Notifications
from proton.vpn.app.gtk.widgets.vpn.port_forward_widget import PortForwardRevealer
from proton.vpn.app.gtk.widgets.headerbar.menu.settings.split_tunneling.split_tunneling import \
    SPLIT_TUNNELING_TOGGLE_SETTING_NAME
from proton.vpn.app.gtk.widgets.vpn.serverlist.icons import CountryFlagIcon
from proton.vpn import logging

logger = logging.getLogger(__name__)

SPLIT_TUNNELING_APP_RESTART_MESSAGE = \
    "Split tunneling enabled. Remember to restart affected apps."


class VPNConnectionStatusWidget(Gtk.Box):  # pylint: disable=too-many-instance-attributes
    """Displays the current connection status."""
    MAXIMUM_SESSIONS_ERROR = "You've reached your maximum device limit. " \
        "To reconnect to VPN, please disconnect from another device."

    def __init__(
        self, controller: Controller,
        notifications: Notifications,
    ):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)

        self.set_name("vpn-connection-status-widget")
        self._controller = controller
        self._notifications = notifications

        self._protected_pixbuf: GdkPixbuf.Pixbuf
        self._unprotected_pixbuf: GdkPixbuf.Pixbuf
        self._fastest_pixbuf: GdkPixbuf.Pixbuf

        self._status_title_row: Gtk.Box
        self._status_icon: Gtk.Image
        self._status_spinner: Gtk.Spinner
        self._status_title_label: Gtk.Label

        self._connection_details_box: Gtk.Grid
        self._connection_details_icon: Gtk.Image
        self._connection_details_title: Gtk.Label
        self._connection_details_subtitle: Gtk.Label

        self._error_detail_label: Gtk.Label
        self._port_forward_revealer: PortForwardRevealer

        self.append(self._build_status_box())

    def _build_status_box(self) -> Gtk.Box:
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        box.set_name("vpn-status-box")

        self._protected_pixbuf = icons.get(
            Path("connection-status/protected.svg"), width=24, height=24)
        self._unprotected_pixbuf = icons.get(
            Path("connection-status/unprotected.svg"), width=24, height=24)
        self._fastest_pixbuf = icons.get(Path("connection-status/fastest.svg"), width=36, height=24)

        self._status_title_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        self._status_title_row.set_name("status-title-row")
        self._status_title_row.set_halign(Gtk.Align.CENTER)
        self._status_title_row.add_css_class("unprotected")

        self._status_icon = Gtk.Image.new_from_paintable(
            Gdk.Texture.new_for_pixbuf(self._unprotected_pixbuf)
        )
        self._status_icon.set_name("status-icon")
        self._status_icon.set_size_request(
            self._unprotected_pixbuf.get_width(), self._unprotected_pixbuf.get_height()
        )
        self._status_icon.set_valign(Gtk.Align.CENTER)

        self._status_spinner = Gtk.Spinner()
        self._status_spinner.set_size_request(
            self._unprotected_pixbuf.get_width(), self._unprotected_pixbuf.get_height()
        )
        self._status_spinner.set_valign(Gtk.Align.CENTER)
        self._status_spinner.set_visible(False)

        self._status_title_label = Gtk.Label(label="")
        self._status_title_label.set_name("status-title-label")
        self._status_title_label.add_css_class("title-4")

        self._status_title_row.append(self._status_icon)
        self._status_title_row.append(self._status_spinner)
        self._status_title_row.append(self._status_title_label)

        self._connection_details_box = Gtk.Grid()
        self._connection_details_box.set_name("connection-details-box")
        self._connection_details_box.set_column_spacing(8)
        self._connection_details_box.set_halign(Gtk.Align.START)

        self._connection_details_icon = Gtk.Image()
        self._connection_details_icon.set_halign(Gtk.Align.START)
        self._connection_details_icon.set_valign(Gtk.Align.START)
        self._connection_details_icon.set_size_request(36, 24)

        self._connection_details_title = Gtk.Label()
        self._connection_details_title.set_name("connection-details-title")
        self._connection_details_title.add_css_class("title-4")
        self._connection_details_title.set_halign(Gtk.Align.START)

        self._connection_details_subtitle = Gtk.Label()
        self._connection_details_subtitle.set_name("connection-details-subtitle")
        self._connection_details_subtitle.set_halign(Gtk.Align.START)

        self._connection_details_box.attach(self._connection_details_icon, 0, 0, 1, 1)
        self._connection_details_box.attach(self._connection_details_title, 1, 0, 1, 1)
        self._connection_details_box.attach(self._connection_details_subtitle, 1, 1, 1, 1)

        self._port_forward_revealer = PortForwardRevealer(self._notifications)
        self._connection_details_box.attach(self._port_forward_revealer, 1, 2, 1, 1)

        self._error_detail_label = Gtk.Label(label="")
        self._error_detail_label.set_name("error-detail-label")
        self._error_detail_label.set_halign(Gtk.Align.CENTER)

        box.append(self._status_title_row)
        box.append(self._error_detail_label)
        box.append(self._connection_details_box)

        return box

    @property
    def status_message(self) -> str:
        """Returns the connection status message being displayed to the user."""
        return self._status_title_label.get_text()

    def connection_status_update(self, connection_state: states.State):
        """This method is called by VPNWidget whenever the VPN connection status changes."""
        disconnected = isinstance(connection_state, states.Disconnected)
        disconnecting = isinstance(connection_state, states.Disconnecting)
        connecting = isinstance(connection_state, states.Connecting)
        connected = isinstance(connection_state, states.Connected)
        error = isinstance(connection_state, states.Error)
        reconnecting = connection_state.context.reconnection

        if not error:
            self._error_detail_label.set_text("")

        if connecting or (disconnecting and reconnecting):
            self._show_spinner()
            self._set_status_title("Connecting...", None)
        elif connected:
            self._show_icon(self._protected_pixbuf)
            self._set_status_title("Protected", "protected")
            if self._split_tunneling_enabled:
                self._notifications.show_info_message(
                    message=SPLIT_TUNNELING_APP_RESTART_MESSAGE
                )
        elif disconnecting and not reconnecting:
            self._show_spinner()
            self._set_status_title("Disconnecting...", None)
        elif error:
            self._show_icon(None)
            self._set_status_title("Connection error", None)
            self._on_connection_error(connection_state)
        elif disconnected:
            self._show_icon(self._unprotected_pixbuf)
            self._set_status_title("Unprotected", "unprotected")

        self._update_connection_details(
            connection_state.context.connection,
            disconnected and not reconnecting
        )

        self._port_forward_revealer.on_new_state(connection_state)

    def _show_spinner(self):
        self._status_icon.set_visible(False)
        self._status_spinner.set_visible(True)
        self._status_spinner.start()

    def _show_icon(self, pixbuf):
        self._status_spinner.stop()
        self._status_spinner.set_visible(False)
        if pixbuf is not None:
            self._status_icon.set_from_paintable(Gdk.Texture.new_for_pixbuf(pixbuf))
            self._status_icon.set_size_request(pixbuf.get_width(), pixbuf.get_height())
            self._status_icon.set_visible(True)
        else:
            self._status_icon.set_visible(False)

    def _set_status_title(self, text: str, css_class: Optional[str]):
        self._status_title_label.set_text(text)
        for cls in ("protected", "unprotected"):
            if cls == css_class:
                self._status_title_row.add_css_class(cls)
            else:
                self._status_title_row.remove_css_class(cls)

    def _on_connection_error(self, connection_state: states.Error):
        last_connection_event = connection_state.context.event
        error_detail = None
        if isinstance(last_connection_event, events.TunnelSetupFailed):
            error_detail = "Tunnel setup failed"
        elif isinstance(last_connection_event, events.AuthDenied):
            error_detail = "Authentication denied"
        elif isinstance(last_connection_event, events.Timeout):
            error_detail = "Timeout"
        elif isinstance(last_connection_event, events.DeviceDisconnected):
            error_detail = "Device disconnected"
        elif isinstance(last_connection_event, events.MaximumSessionsReached):
            error_detail = "Session limit reached"
            self._notifications.show_error_dialog(
                message=self.MAXIMUM_SESSIONS_ERROR,
                title="Connection error: session limit reached"
            )
        if error_detail:
            self._error_detail_label.set_text(error_detail)

    def _update_connection_details(self, connection, disconnected: bool):
        if not self._controller.user_logged_in:
            # State updates can arrive via GLib.idle_add after the user has
            # logged out, at which point session data is already cleared.
            return

        if disconnected:
            pixbuf = self._fastest_pixbuf
            self._connection_details_icon.set_from_paintable(Gdk.Texture.new_for_pixbuf(pixbuf))
            is_free = self._controller.user_tier == TierEnum.FREE
            if is_free:
                self._connection_details_title.set_text("Fastest free server")
                self._connection_details_subtitle.set_text("Auto-selected from free locations")
            else:
                self._connection_details_title.set_text("Fastest country")
                self._connection_details_subtitle.set_text("")
        else:
            server_name = connection.server_name
            logical_server = self._controller.server_list.get_by_name(server_name)
            is_secure_core = ServerFeatureEnum.SECURE_CORE in logical_server.features

            new_connection_details_icon = self._build_connection_details_icon(
                logical_server, is_secure_core)
            self._connection_details_box.remove(self._connection_details_icon)
            self._connection_details_icon = new_connection_details_icon
            self._connection_details_box.attach(self._connection_details_icon, 0, 0, 1, 1)

            self._connection_details_title.set_text(logical_server.exit_country_name)
            if is_secure_core:
                self._connection_details_subtitle.set_label(
                    f"Via {logical_server.entry_country_name}")
            else:
                self._connection_details_subtitle.set_label(
                    f"{logical_server.location} - {server_name}")

    def _build_connection_details_icon(self, logical_server, is_secure_core: bool) -> Gtk.Image:
        if is_secure_core:
            return DoubleFlagIcon(
                exit_country_code=logical_server.exit_country,
                entry_country_code=logical_server.entry_country,
            )
        return CountryFlagIcon(logical_server.exit_country)

    @property
    def _split_tunneling_enabled(self) -> bool:
        """Check if split tunneling is enabled."""
        return cast(bool, self._controller.get_setting_attr(SPLIT_TUNNELING_TOGGLE_SETTING_NAME))
