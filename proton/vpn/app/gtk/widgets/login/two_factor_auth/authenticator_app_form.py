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
from gi.repository import GObject

from proton.vpn import logging

from proton.vpn.app.gtk import Gtk
from proton.vpn.app.gtk.widgets.login.two_factor_auth.authenticate_button import AuthenticateButton

logger = logging.getLogger(__name__)


class AuthenticatorAppForm(Gtk.Box):  # pylint: disable=too-many-instance-attributes
    """
    Implements the UI for TOTP authentication. Once the right 2FA code
    is provided, it emits the `two-factor-auth-successful` signal.
    """
    TWOFA_HELP_LABEL = "6-digit authentication code"
    TWOFA_ENTRY_PLACEHOLDER = "123456"
    TWOFA_ENTRY_LIMIT_CLARIFICATION = ""

    RECOVERY_HELP_LABEL = "Recovery code"
    RECOVERY_ENTRY_PLACEHOLDER = "y5d6132f"
    RECOVERY_ENTRY_LIMIT_CLARIFICATION = "Each code can only be used once"

    RECOVERY_TOGGLE_AUTHENICATION_MODE_LABEL = "Use 6-digit authentication code"
    TWOFA_TOGGLE_AUTHENICATION_MODE_LABEL = "Use recovery code"

    TWOFA_REQUIRED_CHARACTERS = 6
    RECOVERY_REQUIRED_CHARACTERS = 8

    def __init__(self, authenticate_button: AuthenticateButton = None):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=30)
        self.set_name("two-factor-auth-form")
        self._display_2fa_mode = True

        self._entry_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.pack_start(
            self._entry_box,
            expand=False, fill=False, padding=0
        )

        # pylint: disable=R0801
        self._code_entry = Gtk.Entry()
        self._code_entry.connect(
            "changed", self._on_entry_changed
        )
        self._code_entry.set_input_purpose(Gtk.InputPurpose.FREE_FORM)

        self._entry_limit_clarification_label = Gtk.Label()
        self._entry_limit_clarification_label.set_halign(Gtk.Align.START)
        self._entry_limit_clarification_label.get_style_context().add_class("dim-label")
        self._entry_limit_clarification_label.set_line_wrap(True)

        self._help_label = Gtk.Label()
        self._help_label.set_halign(Gtk.Align.START)
        # Pack the help label and the code entry in the entry box
        self._entry_box.pack_start(
            self._help_label, expand=False, fill=False, padding=0
        )
        self._entry_box.pack_start(
            self._code_entry, expand=False, fill=False, padding=0
        )
        self._entry_box.pack_start(
            self._entry_limit_clarification_label, expand=False, fill=False, padding=0
        )

        # Box is used to group the authenticate button and the toggle authentication mode button.
        self._button_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        self.pack_start(
            self._button_box,
            expand=False, fill=False, padding=5
        )

        self._authenticate_button = authenticate_button or AuthenticateButton()
        self._authenticate_button.connect(
            "clicked", self._on_authenticate_button_clicked
        )
        self._button_box.pack_start(
            self._authenticate_button,
            expand=False, fill=False, padding=0
        )

        # Button used to toggle between 2FA and recovery mode.
        self._toggle_authentication_mode_button = Gtk.Button(label="")
        self._toggle_authentication_mode_button.get_style_context().add_class("secondary")
        self._toggle_authentication_mode_button.set_halign(Gtk.Align.FILL)
        self._toggle_authentication_mode_button.set_hexpand(True)
        self._toggle_authentication_mode_button.connect(
            "clicked", self._on_toggle_authentication_mode_clicked
        )
        self._button_box.pack_start(
            self._toggle_authentication_mode_button,
            expand=False, fill=False, padding=0
        )

        # Pressing enter on the password entry triggers the clicked event
        # on the login button.
        self._code_entry.connect("activate", lambda _: self._on_authenticate_button_clicked)
        self._display_2fa_ui()
        self.reset()

    def _on_toggle_authentication_mode_clicked(self, _):
        self._display_2fa_mode = not self._display_2fa_mode

        if self._display_2fa_mode:
            self._display_2fa_ui()
        else:
            self._display_recovery_ui()

        self._code_entry.grab_focus()

    def _display_2fa_ui(self):
        self.code_entry_placeholder = self.TWOFA_ENTRY_PLACEHOLDER
        self.help_label = self.TWOFA_HELP_LABEL
        self.toggle_authentication_mode_button_label = \
            self.TWOFA_TOGGLE_AUTHENICATION_MODE_LABEL
        self.limit_clarification = self.TWOFA_ENTRY_LIMIT_CLARIFICATION

        self._authenticate_button.enable = self.entry_has_required_amount_of_characters

    def _display_recovery_ui(self):
        self.code_entry_placeholder = self.RECOVERY_ENTRY_PLACEHOLDER
        self.help_label = self.RECOVERY_HELP_LABEL
        self.toggle_authentication_mode_button_label = \
            self.RECOVERY_TOGGLE_AUTHENICATION_MODE_LABEL
        self.limit_clarification = self.RECOVERY_ENTRY_LIMIT_CLARIFICATION

        self._authenticate_button.enable = self.entry_has_required_amount_of_characters

    def _on_entry_changed(self, _):
        """Toggles login button state based on username and password lengths."""
        self._authenticate_button.enable = self.entry_has_required_amount_of_characters

    def reset(self):
        """Resets the state of the login/2fa forms."""
        self.two_factor_auth_code = ""
        self._authenticate_button.enable = False
        self._code_entry.grab_focus()

    @property
    def entry_has_required_amount_of_characters(self) -> bool:
        """Returns if the entry has the required amount of characters."""
        return (
            self._display_2fa_mode
            and len(self.code.strip()) == self.TWOFA_REQUIRED_CHARACTERS
            or
            not self._display_2fa_mode
            and len(self.code.strip()) == self.RECOVERY_REQUIRED_CHARACTERS
        )

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
    def limit_clarification(self) -> str:
        """Returns the limit clarification text within `limit_clarification`"""
        return self._entry_limit_clarification_label.get_text()

    @limit_clarification.setter
    def limit_clarification(self, newvalue: str):
        """Sets the limit clarification text within `limit_clarification`"""
        self._entry_limit_clarification_label.set_label(newvalue)

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
    def toggle_authentication_mode_button_label(self) -> str:
        """Returns the label text within `toggle_authentication_mode_button`"""
        return self._toggle_authentication_mode_button.get_label()

    @toggle_authentication_mode_button_label.setter
    def toggle_authentication_mode_button_label(self, newvalue):
        """Sets the label text within `toggle_authentication_mode_button`"""
        self._toggle_authentication_mode_button.set_label(newvalue)

    def _on_authenticate_button_clicked(self, _):
        """Called when the authenticate button is clicked."""
        self.emit("authenticate-button-clicked", self.two_factor_auth_code)

    @GObject.Signal
    def authenticate_button_clicked(self, totp_code: str):
        """Signal emitted after the authenticate button is clicked."""

    @GObject.Signal
    def toggle_authentication_mode_button_clicked(self):
        """Signal emitted after the toggle authentication mode button is clicked."""

    def toggle_authentication_button_click(self):
        """Emulates the click of a button.
        This method was made public for testing purposes.
        """
        self._toggle_authentication_mode_button.clicked()

    def authenticate_button_click(self):
        """Submits the 2FA form."""
        self._authenticate_button.clicked()

    @property
    def authenticate_button_enabled(self):
        """Returns if the authenticate button is enabled."""
        return self._authenticate_button.enable
