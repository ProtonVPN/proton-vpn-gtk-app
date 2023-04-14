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
from typing import Union, TYPE_CHECKING

from proton.vpn.app.gtk.controller import Controller
from proton.vpn.app.gtk import Gtk
from proton.vpn.app.gtk.widgets.main.exception_handler import ExceptionHandler
from proton.vpn.app.gtk.widgets.login.login_widget import LoginWidget
from proton.vpn.app.gtk.widgets.main.notification_bar import NotificationBar
from proton.vpn.app.gtk.widgets.vpn import VPNWidget
from proton.vpn.app.gtk.widgets.main.loading_widget import LoadingWidget
from proton.vpn.app.gtk.widgets.main.notifications import Notifications

if TYPE_CHECKING:
    from proton.vpn.app.gtk.app import MainWindow


# pylint: disable=too-many-instance-attributes
class MainWidget(Gtk.Overlay):
    """
    Main Proton VPN widget. It switches between the LoginWidget and the
    VPNWidget, depending on whether the user is logged in or not.
    """
    ERROR_DIALOG_PRIMARY_TEXT = "Something went wrong"
    SESSION_EXPIRED_ERROR_MESSAGE = "Your session is invalid. "\
        "Please login to re-authenticate."
    SESSION_EXPIRED_ERROR_TITLE = "Invalid Session"

    def __init__(self, controller: Controller, main_window: "MainWindow",
                 notifications: Notifications = None):
        super().__init__()
        self.main_widget = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.main_widget.set_name("main-widget")

        self.loading_widget = LoadingWidget()
        self.add(self.main_widget)
        self.add_overlay(self.loading_widget)

        self._active_widget = None
        self._controller = controller
        self._main_window = main_window

        exception_handler = ExceptionHandler(main_widget=self)
        self.notifications = notifications or Notifications(
            main_window, NotificationBar()
        )
        self.main_widget.pack_start(
            self.notifications.notification_bar,
            expand=False, fill=False, padding=0
        )
        self.login_widget = self._create_login_widget()
        self.vpn_widget = self._create_vpn_widget()

        self.connect("show", lambda *_: self.initialize_visible_widget())
        self.connect("realize", lambda *_: exception_handler.enable())
        self.connect("unrealize", lambda *_: exception_handler.disable())
        self._main_window.header_bar.menu.connect(
            "user-logged-out", self._on_user_logged_out
        )

    @property
    def active_widget(self):
        """Returns the active widget."""
        return self._active_widget

    @active_widget.setter
    def active_widget(self, widget: Union[LoginWidget, VPNWidget]):
        """Sets the active widget. That is, the widget to be shown
        to the user."""
        if self._active_widget:
            self.main_widget.remove(self._active_widget)
        self._active_widget = widget
        self.main_widget.pack_start(self._active_widget, expand=True, fill=True, padding=0)

    def initialize_visible_widget(self):
        """
        Initializes the widget by showing either the vpn widget or the
        login widget depending on whether the user is authenticated or not.
        """
        if self._controller.user_logged_in:
            self._display_vpn_widget()
        else:
            self._display_login_widget()

    def show_error_message(
        self, error_message: str, blocking: bool = False,
        error_title: str = None
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

    def session_expired(self):
        """This method is called by the exception handler once the session
        expires."""
        self.notifications.show_error_dialog(
            title=self.SESSION_EXPIRED_ERROR_TITLE,
            message=self.SESSION_EXPIRED_ERROR_MESSAGE
        )
        self._display_login_widget()

    def _on_user_logged_in(self, _login_widget: LoginWidget):
        self._display_vpn_widget()

    def _on_user_logged_out(self, *_):
        self._display_login_widget()

    def _hide_loading_widget(self, *_):
        self.loading_widget.hide()

    def _create_login_widget(self) -> LoginWidget:
        login_widget = LoginWidget(self._controller)
        login_widget.connect("user-logged-in", self._on_user_logged_in)
        return login_widget

    def _create_vpn_widget(self) -> VPNWidget:
        vpn_widget = VPNWidget(
            controller=self._controller,
            main_window=self._main_window
        )
        vpn_widget.connect(
            "vpn-widget-ready", self._hide_loading_widget
        )
        return vpn_widget

    def _display_vpn_widget(self):
        self._main_window.header_bar.menu.logout_enabled = True
        self.loading_widget.show()
        self.active_widget = self.vpn_widget
        self.vpn_widget.load(self._controller.user_tier)

    def _display_login_widget(self):
        self._main_window.header_bar.menu.logout_enabled = False
        self.loading_widget.hide()  # Required on session expired while loading VPN widget.
        self.active_widget = self.login_widget
        self.login_widget.reset()
        self.login_widget.show_all()
