"""
This module defines the main widget. The main widget is the widget which
exposes all the available app functionality to the user.


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
from typing import Union, TYPE_CHECKING, Optional

from proton.vpn.connection import states
from proton.vpn.app.gtk import Gtk
from proton.vpn.app.gtk.widgets.login.login_widget import LoginWidget
from proton.vpn.app.gtk.widgets.main.notification_bar import NotificationBar
from proton.vpn.app.gtk.widgets.vpn import VPNWidget
from proton.vpn.app.gtk.utils.safe_signal_connect import safe_signal_connect
from proton.vpn.app.gtk.widgets.main.loading_widget import OverlayWidget, DefaultLoadingWidget
from proton.vpn.app.gtk.widgets.main.notifications import Notifications
from proton.vpn.app.gtk.util import connect_once

if TYPE_CHECKING:
    from proton.vpn.app.gtk.controller import Controller
    from proton.vpn.app.gtk.app import MainWindow


# pylint: disable=too-many-instance-attributes
class MainWidget(Gtk.Overlay):
    """
    Main Proton VPN widget. It switches between the LoginWidget and the
    VPNWidget, depending on whether the user is logged in or not.
    """
    ERROR_DIALOG_PRIMARY_TEXT = "Something went wrong"
    SESSION_EXPIRED_ERROR_MESSAGE = "Your session has expired. "\
        "Please sign in again."
    SESSION_EXPIRED_ERROR_TITLE = "Invalid Session"

    def __init__(
        self, controller: "Controller", main_window: "MainWindow",
        overlay_widget: OverlayWidget, notifications: Optional[Notifications] = None
    ):
        super().__init__()
        self.set_name("main-widget")

        self.main_layout = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.main_layout.set_name("main-layout")

        self.content_layout = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.content_layout.set_name("content-layout")

        self._overlay_widget = overlay_widget
        self.main_layout.append(self.content_layout)
        self.set_child(self.main_layout)
        self.add_overlay(self._overlay_widget)

        self._active_widget = None
        self._controller = controller
        self._main_window = main_window
        self._connected_signals: list[tuple[int, Gtk.Widget]] = []

        self._notifications = notifications or Notifications(
            main_window, NotificationBar()
        )
        self.main_layout.prepend(self.notifications.notification_bar)
        self.login_widget = self._create_login_widget()
        self.vpn_widget = None

        safe_signal_connect(self, "realize", self._register_to_exception_handler)
        safe_signal_connect(self, "realize", self._init_on_realize)
        safe_signal_connect(self, "unrealize", self._unregister_from_exception_handler)
        safe_signal_connect(
            self._main_window.header_bar.menu,
            "user-logged-out",
            self._on_user_logged_out
        )

    def _register_to_exception_handler(self, *_):
        self._controller.exception_handler.main_widget = self

    def _unregister_from_exception_handler(self, *_):
        self._controller.exception_handler.main_widget = None

    def _init_on_realize(self, *_):
        self.initialize_visible_widget()

    @property
    def notifications(self) -> Notifications:
        """Returns the notifications object."""
        return self._notifications

    @property
    def active_widget(self):
        """Returns the active widget."""
        return self._active_widget

    @active_widget.setter
    def active_widget(self, widget: Union[LoginWidget, VPNWidget]):
        """Sets the active widget. That is, the widget to be shown
        to the user."""
        if self._active_widget:
            self.content_layout.remove(self._active_widget)
        self._active_widget = widget
        self.content_layout.append(self._active_widget)

    _STATE_CSS_CLASSES = {
        states.Connected: "vpn-connected",
        states.Connecting: "vpn-connecting",
        states.Disconnecting: "vpn-disconnecting",
        states.Disconnected: "vpn-disconnected",
        states.Error: "vpn-error",
    }

    def set_background_gradient(self, state: Optional[states.State]):
        """Sets the gradient on the main widget background for the given VPN state.

        :param state: a connection state instance, or None to clear all.
        """
        for css_class in self._STATE_CSS_CLASSES.values():
            self.remove_css_class(css_class)
        if state and (css_class := self._STATE_CSS_CLASSES.get(type(state))):
            self.add_css_class(css_class)

    def initialize_visible_widget(self):
        """
        Initializes the widget by showing either the vpn widget or the
        login widget depending on whether the user is authenticated or not.
        """
        if self._controller.user_logged_in:
            self._display_vpn_widget()
            connect_once(
                self.vpn_widget,
                "vpn-widget-ready",
                self._controller.run_startup_actions
            )
        else:
            self._display_login_widget()

    def show_error_message(
        self, error_message: str, blocking: bool = False,
        error_title: Optional[str] = None
    ):
        """
        Shows an error message to the user. The message is hidden after the
        specified amount of time.
        :param error_message: error message to be shown.
        :param blocking: whether the error message should require
        confirmation from the user or not.
        """
        if blocking:
            self.notifications.show_error_dialog(error_message, error_title)
        else:
            self.notifications.show_error_message(error_message)

    def on_session_expired(self):
        """This method is called by the exception handler once the session
        expires."""
        self.notifications.show_error_dialog(
            title=self.SESSION_EXPIRED_ERROR_TITLE,
            message=self.SESSION_EXPIRED_ERROR_MESSAGE
        )
        self._display_login_widget()

    def logout(self):
        """Logs out the user."""
        self._main_window.header_bar.menu.logout_button_click()

    def _on_user_logged_in(self, _login_widget: LoginWidget):
        self._display_vpn_widget()

    def _on_user_logged_out(self, *_):
        self._display_login_widget()

    def _hide_overlay_widget(self, *_):
        self._overlay_widget.hide()

    def _create_login_widget(self) -> LoginWidget:
        login_widget = LoginWidget(
            self._controller, self.notifications,
            self._overlay_widget, self._main_window
        )
        safe_signal_connect(login_widget, "user-logged-in", self._on_user_logged_in)
        return login_widget

    def _create_vpn_widget(self) -> VPNWidget:
        vpn_widget = VPNWidget(
            controller=self._controller,
            main_window=self._main_window,
            notifications=self.notifications
        )
        safe_signal_connect(
            vpn_widget, "vpn-widget-ready", self._hide_overlay_widget
        )
        signal_id = safe_signal_connect(
            vpn_widget,
            "connection-state-changed",
            self._change_gradient_on_connection_state_change
        )
        self._connected_signals.append((signal_id, vpn_widget))

        return vpn_widget

    def _change_gradient_on_connection_state_change(self, _, state):
        self.set_background_gradient(state)

    def _display_vpn_widget(self):
        self.vpn_widget = self._create_vpn_widget()
        self._main_window.header_bar.menu.logout_enabled = True
        self._main_window.header_bar.menu.settings_enabled = True
        self._overlay_widget.show(
            DefaultLoadingWidget("Loading app...")
        )
        self.active_widget = self.vpn_widget
        self.vpn_widget.load()

    def _display_login_widget(self):
        self.set_background_gradient(None)
        for signal_id, widget in self._connected_signals:
            widget.disconnect(signal_id)
        self._connected_signals.clear()
        self._main_window.header_bar.menu.logout_enabled = False
        self._main_window.header_bar.menu.settings_enabled = False
        # Close the settings window in case the session expires with the settings windows open.
        self._main_window.header_bar.menu.close_settings_window()
        self._overlay_widget.hide()  # Required on session expired while loading VPN widget.
        self.active_widget = self.login_widget
        self.login_widget.reset()
