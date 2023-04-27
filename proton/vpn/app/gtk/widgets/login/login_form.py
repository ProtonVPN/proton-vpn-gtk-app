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

from gi.repository import GdkPixbuf, GLib, GObject

from proton.vpn import logging

from proton.vpn.app.gtk import Gtk
from proton.vpn.app.gtk.assets import ASSETS_PATH
from proton.vpn.app.gtk.controller import Controller
from proton.vpn.app.gtk.widgets.login.logo import ProtonVPNLogo
from proton.vpn.app.gtk.widgets.main.notifications import Notifications

logger = logging.getLogger(__name__)


class LoginForm(Gtk.Box):  # pylint: disable=R0902
    """It implements the login form. Once the user is authenticated, it
    emits the `user-authenticated` signal.

    Note that 2FA is not implemented by this widget. For that see
    TwoFactorAuthForm.

    """
    INVALID_USERNAME_MESSAGE = "Invalid username."
    INCORRECT_CREDENTIALS_MESSAGE = "Incorrect credentials."

    def __init__(self, controller: Controller, notifications: Notifications):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=30)
        self.set_name("login-form")
        self._controller = controller
        self._notifications = notifications

        self.pack_start(ProtonVPNLogo(), expand=False, fill=True, padding=0)

        self._username_entry = Gtk.Entry()
        self._username_entry.set_placeholder_text("Username")
        self._username_entry.set_input_purpose(Gtk.InputPurpose.FREE_FORM)
        self.pack_start(self._username_entry, expand=False, fill=False, padding=0)

        self._password_entry = PasswordEntry()
        self._password_entry.set_placeholder_text("Password")
        self.pack_start(self._password_entry, expand=False, fill=False, padding=0)

        self._login_button = Gtk.Button(label="Login")
        self._login_button.connect("clicked", self._on_login_button_clicked)
        self._login_button.get_style_context().add_class("primary")
        self._login_button.get_style_context().add_class("spaced")
        self._login_button.set_halign(Gtk.Align.CENTER)
        # By default, the button should never be clickable, as username and
        # password fields are empty and users need to actively provide an input
        # to unlock the login button.
        self._login_button.set_property("sensitive", False)
        self.pack_start(self._login_button, expand=False, fill=False, padding=0)

        # Listen to key entries so that the login button can be "unlocked"
        # once username and password are provided.
        self._password_entry.connect(
            "changed", self._on_entry_changed
        )
        self._username_entry.connect(
            "changed", self._on_entry_changed
        )

        # Allows both entries to react to 'Enter' button
        self._username_entry.connect("activate", self._on_press_enter)
        self._password_entry.connect("activate", self._on_press_enter)

        self._login_spinner = Gtk.Spinner()
        self.pack_start(self._login_spinner, expand=False, fill=False, padding=0)

        self.pack_end(LoginLinks(), expand=False, fill=False, padding=0)

    def _on_press_enter(self, _):
        if not self._login_button.get_property("sensitive"):
            return

        self._login_button.clicked()

    def _on_login_button_clicked(self, _):
        logger.info("Clicked on login", category="UI", subcategory="LOGIN", event="CLICK")
        self._login_spinner.start()
        future = self._controller.login(self.username, self.password)
        future.add_done_callback(
            lambda future: GLib.idle_add(self._on_login_result, future)
        )

    def _on_login_result(self, future: Future):
        try:
            result = future.result()
        except ValueError as error:
            self._notifications.show_error_message(self.INVALID_USERNAME_MESSAGE)
            logger.debug(error, category="APP", subcategory="LOGIN", event="RESULT")
            self.emit("login-error")
            return
        finally:
            self._login_spinner.stop()

        if result.authenticated:
            self._signal_user_authenticated(result.twofa_required)
        else:
            self._notifications.show_error_message(self.INCORRECT_CREDENTIALS_MESSAGE)
            logger.debug(
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
        self.password = ""
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
        self._login_button.clicked()

    def username_enter(self):
        """Submits the login form from the username entry.
        This property was made available mainly for testing purposes."""
        self._username_entry.emit("activate")

    def password_enter(self):
        """Submits the login form from the password entry.
        This property was made available mainly for testing purposes."""
        self._password_entry.emit("activate")


class PasswordEntry(Gtk.Entry):
    """
    Entry used to introduce the password in the login form.

    On top of the inherited functionality from Gtk.Entry, an icon is shown
    inside the text entry to show or hide the password.

    By default, the text (password) introduced in the entry is not show.
    Therefore, the icon to be able to show the text is displayed. Once this
    icon is pressed, the text is revealed and the icon to hide the password
    is shown instead.
    """
    def __init__(self):
        super().__init__()
        self.set_input_purpose(Gtk.InputPurpose.PASSWORD)
        self.set_visibility(False)
        # Load icon to hide the password.
        eye_dirpath = ASSETS_PATH / "icons" / "eye"
        hide_fp = str(eye_dirpath / "hide.svg")
        self._hide_pixbuff = GdkPixbuf.Pixbuf.new_from_file_at_scale(
            filename=hide_fp,
            width=18,
            height=18,
            preserve_aspect_ratio=True
        )
        # Load icon to show the password.
        show_fp = str(eye_dirpath / "show.svg")
        self._show_pixbuff = GdkPixbuf.Pixbuf.new_from_file_at_scale(
            filename=show_fp,
            width=18,
            height=18,
            preserve_aspect_ratio=True
        )
        # By default, the password is not shown. Therefore, the icon to
        # be able to show the password is shown.
        self.set_icon_from_pixbuf(
            Gtk.EntryIconPosition.SECONDARY,
            self._show_pixbuff
        )
        self.set_icon_activatable(
            Gtk.EntryIconPosition.SECONDARY,
            True
        )
        self.connect(
            "icon-press", self._on_change_password_visibility_icon_press
        )

    def _on_change_password_visibility_icon_press(
            self, gtk_entry_object,
            gtk_icon_object, gtk_event  # pylint: disable=W0613
    ):
        """Changes password visibility, updating accordingly the icon."""
        is_text_visible = gtk_entry_object.get_visibility()
        gtk_entry_object.set_visibility(not is_text_visible)
        self.set_icon_from_pixbuf(
            Gtk.EntryIconPosition.SECONDARY,
            self._show_pixbuff
            if is_text_visible
            else self._hide_pixbuff
        )


class LoginLinks(Gtk.Box):
    """Links shown in the login widget."""
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        create_account_link = Gtk.LinkButton(
            label="Create Account",
            uri="https://account.protonvpn.com/signup"
        )
        self.pack_start(
            create_account_link, expand=False, fill=False, padding=0
        )
        help_link = Gtk.LinkButton(
            label="Need Help?",
            uri="https://protonvpn.com/support"
        )
        self.pack_end(
            help_link, expand=False, fill=False, padding=0
        )
