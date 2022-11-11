"""
This module defines the main widget. The main widget is the widget which
exposes all the available app functionality to the user.
"""
from typing import Union

from proton.vpn.app.gtk.controller import Controller
from proton.vpn.app.gtk import Gtk
from proton.vpn.app.gtk.widgets.exception_handler import ExceptionHandler
from proton.vpn.app.gtk.widgets.login import LoginWidget
from proton.vpn.app.gtk.widgets.notification_bar import NotificationBar
from proton.vpn.app.gtk.widgets.vpn import VPNWidget
from proton.vpn.app.gtk.widgets.error_messenger import ErrorMessenger


# pylint: disable=too-many-instance-attributes
class MainWidget(Gtk.Box):
    """
    Main Proton VPN widget. It switches between the LoginWidget and the
    VPNWidget, depending on whether the user is logged in or not.
    """
    ERROR_DIALOG_PRIMARY_TEXT = "Something went wrong"
    SESSION_EXPIRED_ERROR_MESSAGE = "Your session is invalid. "\
        "Please login to re-authenticate."
    SESSION_EXPIRED_ERROR_TITLE = "Invalid Session"

    def __init__(self, controller: Controller, main_window: Gtk.ApplicationWindow = None):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self._active_widget = None
        self._controller = controller
        self._application_window = main_window
        exception_handler = ExceptionHandler(main_widget=self)
        notification_bar = NotificationBar()

        self.pack_start(notification_bar, expand=False, fill=False, padding=0)

        self._error_messenger = ErrorMessenger(main_window, notification_bar)

        self.login_widget = LoginWidget(controller)
        self.login_widget.connect("user-logged-in", self._on_user_logged_in)

        self.vpn_widget = VPNWidget(controller)
        self.vpn_widget.connect("user-logged-out", self._on_user_logged_out)
        self.vpn_widget.connect("vpn-connection-error", self._display_connection_error)

        self.connect("show", lambda *_: self.initialize_visible_widget())
        self.connect("realize", lambda *_: exception_handler.enable())
        self.connect("unrealize", lambda *_: exception_handler.disable())

    @property
    def active_widget(self):
        """Returns the active widget."""
        return self._active_widget

    @active_widget.setter
    def active_widget(self, widget: Union[LoginWidget, VPNWidget]):
        """Sets the active widget. That is, the widget to be shown
        to the user."""
        if self._active_widget:
            self.remove(self._active_widget)
        self._active_widget = widget
        self.pack_start(self._active_widget, expand=True, fill=True, padding=0)

    def initialize_visible_widget(self):
        """
        Initializes the widget by showing either the vpn widget or the
        login widget depending on whether the user is authenticated or not.

        Note that the widget should already be flagged as shown when this
        method is called. Otherwise, it won't have effect. For more info:
        https://lazka.github.io/pgi-docs/#Gtk-3.0/classes/Stack.html#Gtk.Stack.set_visible_child
        """
        self._display_widget(
            self.vpn_widget
            if self._controller.user_logged_in else
            self.login_widget
        )

    def _display_connection_error(self, *args):
        _, title, message = args
        self.show_error_message(message, True, title)

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
            self._error_messenger.show_error_dialog(error_message, error_title)
        else:
            self._error_messenger.show_error_bar(error_message)

    def session_expired(self):
        """This method is called by the exception handler once the session
        expires."""
        self.show_error_message(
            self.SESSION_EXPIRED_ERROR_MESSAGE,
            True, self.SESSION_EXPIRED_ERROR_TITLE
        )
        self._display_widget(self.login_widget)
        self.login_widget.reset()

    def _on_user_logged_in(self, _login_widget: LoginWidget):
        self._display_widget(self.vpn_widget)

    def _on_user_logged_out(self, _vpn_widget: VPNWidget):
        self._display_widget(self.login_widget)
        self.login_widget.reset()

    def _display_widget(self, widget: Union[LoginWidget, VPNWidget]):
        self.active_widget = widget
        self.active_widget.show_all()
