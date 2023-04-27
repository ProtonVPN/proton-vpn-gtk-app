"""
This module defines the widget used to display the 2FA form.

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
from proton.vpn.app.gtk.widgets.login.logo import ProtonVPNLogo
from proton.vpn.app.gtk.widgets.main.notifications import Notifications

logger = logging.getLogger(__name__)


class TwoFactorAuthForm(Gtk.Box):  # pylint: disable=too-many-instance-attributes
    """
    Implements the UI for two-factor authentication. Once the right 2FA code
    is provided, it emits the `two-factor-auth-successful` signal.
    """
    SESSION_EXPIRED_MESSAGE = "Session expired. Please login again."
    INCORRECT_TWOFA_CODE_MESSAGE = "Incorrect 2FA code."

    TWOFA_ENTRY_PLACEHOLDER = "Enter your 2FA code here"
    TWOFA_HELP_LABEL = "Enter the 6-digit code."
    TWOFA_BUTTON_LABEL = "Submit 2FA code"
    TWOFA_TOGGLE_AUTHENICATION_MODE_LABEL = "Use recovery code"

    RECOVERY_ENTRY_PLACEHOLDER = "Enter your recovery code here"
    RECOVERY_HELP_LABEL = "Enter the 8-character code."
    RECOVERY_BUTTON_LABEL = "Submit recovery code"
    RECOVERY_TOGGLE_AUTHENICATION_MODE_LABEL = "Use two-factor code"

    TWOFA_REQUIRED_CHARACTERS = 6
    RECOVERY_REQUIRED_CHARACTERS = 8

    def __init__(self, controller: Controller, notifications: Notifications):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=30)
        self.set_name("two-factor-auth-form")
        self._display_2fa_mode = True
        self._controller = controller
        self._notifications = notifications

        # pylint: disable=R0801
        self.pack_start(ProtonVPNLogo(), expand=False, fill=True, padding=0)
        self._code_entry = Gtk.Entry()
        self._code_entry.connect(
            "changed", self._on_entry_changed
        )
        self._code_entry.set_input_purpose(Gtk.InputPurpose.FREE_FORM)
        self.pack_start(
            self._code_entry, expand=False, fill=False, padding=0
        )

        self._help_label = Gtk.Label()
        self._help_label.set_halign(Gtk.Align.START)
        self._help_label.get_style_context().add_class("dim-label")
        self.pack_start(
            self._help_label, expand=False, fill=False, padding=0
        )

        self._submission_button = Gtk.Button()
        self._submission_button.set_halign(Gtk.Align.CENTER)
        self._submission_button.get_style_context().add_class("primary")
        self._submission_button.set_property("sensitive", False)
        self._submission_button.connect(
            "clicked", self._on_submission_button_clicked
        )
        self.pack_start(
            self._submission_button, expand=False, fill=False, padding=0
        )

        self._toggle_authentication_mode_button = Gtk.Button(label="")
        self._toggle_authentication_mode_button.get_style_context().add_class("secondary")
        self._toggle_authentication_mode_button.set_halign(Gtk.Align.CENTER)
        self._toggle_authentication_mode_button.connect(
            "clicked", self._on_toggle_authentication_mode_clicked
        )
        self.pack_start(
            self._toggle_authentication_mode_button,
            expand=False, fill=False, padding=5
        )

        # Pressing enter on the password entry triggers the clicked event
        # on the login button.
        self._code_entry.connect(
            "activate", lambda _: self._submission_button.clicked())

        self._spinner = Gtk.Spinner()
        self.pack_start(self._spinner, expand=False, fill=False, padding=0)

        self._display_2fa_ui()
        self.reset()

    def _on_toggle_authentication_mode_clicked(self, _):
        self._display_2fa_mode = not self._display_2fa_mode

        if self._display_2fa_mode:
            self._display_2fa_ui()
        else:
            self._display_recovery_ui()

        self._code_entry.grab_focus()

    def _on_submission_button_clicked(self, _):
        logger.info("Clicked on login", category="UI", subcategory="LOGIN-2FA", event="CLICK")
        self._spinner.start()
        future = self._controller.submit_2fa_code(
            self.two_factor_auth_code
        )
        future.add_done_callback(
            lambda future: GLib.idle_add(self._on_2fa_submission_result, future)
        )

    def _on_2fa_submission_result(self, future: Future):
        try:
            result = future.result()
        finally:
            self._spinner.stop()

        if not result.authenticated:
            self._notifications.show_error_message(self.SESSION_EXPIRED_MESSAGE)
            logger.debug(
                self.SESSION_EXPIRED_MESSAGE, category="APP",
                subcategory="LOGIN-2FA", event="RESULT"
            )
            self.emit("session-expired")
        elif result.twofa_required:
            self._notifications.show_error_message(self.INCORRECT_TWOFA_CODE_MESSAGE)
            logger.debug(
                self.INCORRECT_TWOFA_CODE_MESSAGE, category="APP",
                subcategory="LOGIN-2FA", event="RESULT"
            )
        else:  # authenticated and 2FA not required
            self._signal_two_factor_auth_successful()

    def _signal_two_factor_auth_successful(self):
        self.emit("two-factor-auth-successful")

    def _display_2fa_ui(self):
        self.code_entry_placeholder = self.TWOFA_ENTRY_PLACEHOLDER
        self.help_label = self.TWOFA_HELP_LABEL
        self.submission_button_label = self.TWOFA_BUTTON_LABEL
        self.toggle_authentication_mode_button_label = \
            self.TWOFA_TOGGLE_AUTHENICATION_MODE_LABEL

        self._submission_button.set_property(
            "sensitive",
            len(self.code.strip()) == self.TWOFA_REQUIRED_CHARACTERS
        )

    def _display_recovery_ui(self):
        self.code_entry_placeholder = self.RECOVERY_ENTRY_PLACEHOLDER
        self.help_label = self.RECOVERY_HELP_LABEL
        self.submission_button_label = self.RECOVERY_BUTTON_LABEL
        self.toggle_authentication_mode_button_label = \
            self.RECOVERY_TOGGLE_AUTHENICATION_MODE_LABEL

        self._submission_button.set_property(
            "sensitive",
            len(self.code.strip()) == self.RECOVERY_REQUIRED_CHARACTERS
        )

    def _on_entry_changed(self, _):
        """Toggles login button state based on username and password lengths."""
        required_characers = self.RECOVERY_REQUIRED_CHARACTERS
        if self._display_2fa_mode:
            required_characers = self.TWOFA_REQUIRED_CHARACTERS

        do_characters_satisfy_req = len(self.code.strip()) == required_characers

        self._submission_button.set_property("sensitive", do_characters_satisfy_req)

    @GObject.Signal
    def two_factor_auth_successful(self):
        """Signal emitted after a successful 2FA."""

    @GObject.Signal
    def session_expired(self):
        """Signal emitted when the session expired and the user has to log in again."""

    def reset(self):
        """Resets the state of the login/2fa forms."""
        self._notifications.hide_message()
        self.two_factor_auth_code = ""
        self._code_entry.grab_focus()

    @property
    def code(self):
        """Returns the content of `code_entry`"""
        return self._code_entry.get_text()

    @code.setter
    def code(self, newvalue):
        """Sets the content of `code_entry`"""
        return self._code_entry.set_text(newvalue)

    @property
    def two_factor_auth_code(self):
        """Returns the code introduced in the 2FA form."""
        return self._code_entry.get_text()

    @two_factor_auth_code.setter
    def two_factor_auth_code(self, code: str):
        """Sets the code in the 2FA form."""
        self._code_entry.set_text(code)

    @property
    def code_entry_placeholder(self) -> str:
        """Sets the placeholder text within `code_entry`"""
        return self._code_entry.get_placeholder_text()

    @code_entry_placeholder.setter
    def code_entry_placeholder(self, newvalue: str):
        """Sets the text within `code_entry`"""
        self._code_entry.set_placeholder_text(newvalue)

    @property
    def help_label(self) -> str:
        """Returns text within `help_label`"""
        return self._help_label.get_label()

    @help_label.setter
    def help_label(self, newvalue: str):
        """Sets the label text within `help_label`"""
        self._help_label.set_label(newvalue)

    @property
    def submission_button_label(self) -> str:
        """Returns the label text within `submission_button`"""
        return self._submission_button.get_label()

    @submission_button_label.setter
    def submission_button_label(self, newvalue):
        """Sets the label text within `submission_button`"""
        self._submission_button.set_label(newvalue)

    @property
    def toggle_authentication_mode_button_label(self) -> str:
        """Returns the label text within `toggle_authentication_mode_button`"""
        return self._toggle_authentication_mode_button.get_label()

    @toggle_authentication_mode_button_label.setter
    def toggle_authentication_mode_button_label(self, newvalue):
        """Sets the label text within `toggle_authentication_mode_button`"""
        self._toggle_authentication_mode_button.set_label(newvalue)

    def submit_two_factor_auth(self):
        """Submits the 2FA form."""
        self._submission_button.clicked()

    def toggle_authentication_button_click(self):
        """Emulates the click of a button.
        This method was made public for testing purposes.
        """
        self._toggle_authentication_mode_button.clicked()

    @property
    def submission_button_enabled(self):
        "Returns the submission button sensitive property"
        return self._submission_button.get_property("sensitive")
