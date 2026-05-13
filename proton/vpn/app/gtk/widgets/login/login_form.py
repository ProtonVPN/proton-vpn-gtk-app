"""
This module defines the widgets required to display the form to
authenticate with username and password.


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
from concurrent.futures import Future

from gi.repository import GLib, GObject

from proton.vpn import logging

from proton.vpn.app.gtk import Gtk
from proton.vpn.app.gtk.controller import Controller
from proton.vpn.app.gtk.utils.safe_signal_connect import safe_signal_connect
from proton.vpn.app.gtk.widgets.login.logo import ProtonVPNLogo
from proton.vpn.app.gtk.widgets.login.password_entry import PasswordEntry
from proton.vpn.app.gtk.widgets.main.notifications import Notifications
from proton.vpn.app.gtk.widgets.main.loading_widget import OverlayWidget, DefaultLoadingWidget

logger = logging.getLogger(__name__)


class LoginForm(Gtk.Box):  # pylint: disable=R0902
    """It implements the login form. Once the user is authenticated, it
    emits the `user-authenticated` signal.

    Note that 2FA is not implemented by this widget. For that see
    TwoFactorAuthForm.

    """
    LOGGING_IN_MESSAGE = "Signing in..."
    INVALID_USERNAME_MESSAGE = "Invalid username."
    INCORRECT_CREDENTIALS_MESSAGE = "Incorrect credentials."

    def __init__(
        self,
        controller: Controller,
        notifications: Notifications,
        overlay_widget: OverlayWidget
    ):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=30)
        self.set_name("login-form")
        self.set_vexpand(True)
        self.set_halign(Gtk.Align.FILL)
        self.set_valign(Gtk.Align.FILL)
        self._controller = controller
        self._notifications = notifications
        self._overlay_widget = overlay_widget

        self.append(ProtonVPNLogo())

        self._username_entry = Gtk.Entry()
        self._username_entry.set_placeholder_text("Username")
        self._username_entry.set_input_purpose(Gtk.InputPurpose.FREE_FORM)
        self.append(self._username_entry)

        self._password_entry = PasswordEntry()
        self._password_entry.set_placeholder_text("Password")
        self.append(self._password_entry)

        self._login_button = Gtk.Button(label="Sign in")
        safe_signal_connect(self._login_button, "clicked", self._on_login_button_clicked)
        self._login_button.add_css_class("primary")
        self._login_button.add_css_class("spaced")
        self._login_button.set_halign(Gtk.Align.CENTER)
        # By default, the button should never be clickable, as username and
        # password fields are empty and users need to actively provide an input
        # to unlock the login button.
        self._login_button.set_property("sensitive", False)
        self.append(self._login_button)

        # Listen to key entries so that the login button can be "unlocked"
        # once username and password are provided.
        safe_signal_connect(
            self._password_entry, "changed", self._on_entry_changed
        )
        safe_signal_connect(
            self._username_entry, "changed", self._on_entry_changed
        )

        # Allows both entries to react to 'Enter' button
        safe_signal_connect(self._username_entry, "activate", self._on_press_enter)
        safe_signal_connect(self._password_entry, "activate", self._on_press_enter)

        self.append(LoginLinks())

    def _on_press_enter(self, _):
        if not self._login_button.get_property("sensitive"):
            return

        self._login_button.emit("clicked")

    def _on_login_button_clicked(self, _):
        logger.info("Clicked on login", category="UI", subcategory="LOGIN", event="CLICK")
        self._overlay_widget.show(
            DefaultLoadingWidget(self.LOGGING_IN_MESSAGE)
        )
        future = self._controller.login(self.username, self.password)
        future.add_done_callback(
            lambda future: GLib.idle_add(self._on_login_result, future)
        )

    def _on_login_result(self, future: Future):
        try:
            result = future.result()
        except ValueError as error:
            self._notifications.show_error_message(self.INVALID_USERNAME_MESSAGE)
            logger.warning(
                error, category="APP", subcategory="LOGIN", event="RESULT",
                exc_info=True
            )
            self.emit("login-error")
            return
        finally:
            self._overlay_widget.hide()

        if result.authenticated:
            self._signal_user_authenticated(result.twofa_required)
        else:
            self._notifications.show_error_message(self.INCORRECT_CREDENTIALS_MESSAGE)
            logger.warning(
                self.INCORRECT_CREDENTIALS_MESSAGE, category="APP",
                subcategory="LOGIN", event="RESULT"
            )
            self.emit("login-error")

    def _on_entry_changed(self, _):
        """Toggles login button state based on username and password lengths."""
        is_username_provided = len(self.username.strip()) > 0
        is_password_provided = len(self.password.strip()) > 0
        is_data_provided = is_username_provided and is_password_provided

        self._login_button.set_property("sensitive", is_data_provided)

    def _signal_user_authenticated(self, two_factor_auth_required: bool):
        self.emit("user-authenticated", two_factor_auth_required)

    @GObject.Signal(name="user-authenticated", arg_types=(bool,))
    def user_authenticated(self, two_factor_auth_required: bool):
        """
        Signal emitted after the user successfully authenticates.
        :param two_factor_auth_required: whether 2FA is required or not.
        """

    @GObject.Signal(name="login-error")
    def login_error(self):
        """Signal emitted when a login error occurred."""

    def reset(self):
        """Resets the state of the login/2fa forms."""
        self._notifications.hide_message()
        self.username = ""
        self.password = ""  # nosec B105
        self._username_entry.grab_focus()

    @property
    def error_message(self) -> str:
        """Return the contents of the error message in the notification bar."""
        return self._notifications.notification_bar.current_message

    @property
    def username(self) -> str:
        """Returns the username introduced in the login form."""
        return self._username_entry.get_text()

    @username.setter
    def username(self, username: str):
        """Sets the username in the login form."""
        self._username_entry.set_text(username)

    @property
    def password(self) -> str:
        """Returns the password introduced in the login form."""
        return self._password_entry.get_text()

    @password.setter
    def password(self, password: str):
        """Sets the password in the login form."""
        self._password_entry.set_text(password)

    @property
    def is_login_button_clickable(self) -> bool:
        """Check if the login button is clickable or not.
        This property was made available mainly for testing purposes."""
        return self._login_button.get_property("sensitive")

    def submit_login(self):
        """Submits the login form.
        This property was made available mainly for testing purposes."""
        self._login_button.emit("clicked")

    def username_enter(self):
        """Submits the login form from the username entry.
        This property was made available mainly for testing purposes."""
        self._username_entry.emit("activate")

    def password_enter(self):
        """Submits the login form from the password entry.
        This property was made available mainly for testing purposes."""
        self._password_entry.emit("activate")


class LoginLinks(Gtk.Box):
    """Links shown in the login widget."""
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        self.set_vexpand(True)
        self.set_valign(Gtk.Align.END)
        create_account_link = Gtk.LinkButton(
            label="Create Account",
            uri="https://account.protonvpn.com/signup?ref=linux"
        )
        create_account_link.set_halign(Gtk.Align.START)
        create_account_link.set_hexpand(True)
        self.append(create_account_link)
        help_link = Gtk.LinkButton(
            label="Need Help?",
            uri="https://protonvpn.com/support"
        )
        help_link.set_halign(Gtk.Align.END)
        help_link.set_hexpand(True)
        self.append(help_link)
