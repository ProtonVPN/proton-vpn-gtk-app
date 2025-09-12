"""
This module defines the widget used to display the security device form.


Copyright (c) 2025 Proton AG

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
from dataclasses import dataclass
from gi.repository import GObject

from proton.vpn.app.gtk import Gtk

from proton.vpn.app.gtk.widgets.login.logo import SecurityKeyLogo
from proton.vpn.app.gtk.widgets.headerbar.menu.settings.common import SettingDescription
from proton.vpn.app.gtk.widgets.login.two_factor_auth.authenticate_button import AuthenticateButton


LEARN_MORE_LINK = '<a href="https://protonvpn.com/support/#">Learn more</a>'


@dataclass
class SecurityKeyFormData:
    """Data class for the security key form."""


class SecurityKeyForm(Gtk.Box):  # pylint: disable=R0902
    """
    Implements the UI for HOTP authentication.
    Once the HOTP code is authenticated,
    it emits the `hotp-auth-successful` signal.
    """
    DESCRIPTION_LABEL = "Insert the U2F or FIDO key linked to your Proton Account. " \
        + LEARN_MORE_LINK
    PIN_CODE_LABEL = "PIN code"

    def __init__(self, authenticate_button: AuthenticateButton = None):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=15)

        self.set_name("security-device-form")

        self._authenticate_button = authenticate_button or AuthenticateButton()
        self._authenticate_button.connect(
            "clicked", self._on_authenticate_button_clicked
        )

        self._instruction_label = SettingDescription(self.DESCRIPTION_LABEL)
        self._instruction_label.get_style_context().remove_class("dim-label")
        self._instruction_label.set_line_wrap(True)
        self._instruction_label.set_property("track-visited-links", False)

        self._pin_code_label = Gtk.Label(label=self.PIN_CODE_LABEL)
        self._pin_code_label.set_halign(Gtk.Align.START)

        self._pin_code_entry = Gtk.Entry()
        self._pin_code_entry.set_input_purpose(Gtk.InputPurpose.FREE_FORM)
        self._pin_code_entry.connect(
            "changed", self._on_pin_code_entry_changed
        )
        self._pin_code_entry.connect("activate", lambda _: self._on_authenticate_button_clicked)

        # Box is used to group the pin code label and the pin code entry.
        self._pin_code_box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL, spacing=10
        )
        self._pin_code_box.pack_start(self._pin_code_label, expand=False, fill=False, padding=0)
        self._pin_code_box.pack_start(self._pin_code_entry, expand=False, fill=False, padding=0)

        self._pin_code_box_revealer = Gtk.Revealer()
        self._pin_code_box_revealer.add(self._pin_code_box)
        self._pin_code_box_revealer.connect(
            "notify::reveal-child", self._on_pin_code_box_revealer_notify_reveal_child
        )

        # Box is used to group the pin code box revealer and the authenticate button.
        self._authenticate_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self._authenticate_box.pack_start(
            self._pin_code_box_revealer, expand=False, fill=False, padding=0
        )
        self._authenticate_box.pack_start(
            self._authenticate_button, expand=False, fill=False, padding=0
        )

        self.pack_start(self._instruction_label, expand=False, fill=False, padding=0)
        self.pack_start(SecurityKeyLogo(), expand=False, fill=False, padding=0)
        self.pack_start(self._authenticate_box, expand=False, fill=False, padding=0)

    def _on_authenticate_button_clicked(self, _):
        """Called when the authenticate button is clicked."""
        self._authenticate_user_without_pin_code()

    def _authenticate_user_without_pin_code(self):
        self.emit("authenticate-button-clicked", SecurityKeyFormData())

    def _on_pin_code_box_revealer_notify_reveal_child(self, *_):
        """Called when the pin code box revealer is notified of a reveal child change."""
        self._authenticate_button.enable = len(self._pin_code_entry.get_text().strip()) > 0

    def _on_pin_code_entry_changed(self, _):
        """Toggles pin code entry state based on pin code length."""
        self._authenticate_button.enable = len(self._pin_code_entry.get_text().strip()) > 0

    def reset(self):
        """Resets the widget to its initial state."""
        self._pin_code_box_revealer.set_reveal_child(False)
        self._pin_code_entry.set_text("")
        self._authenticate_button.enable = True

    @GObject.Signal
    def authenticate_button_clicked(self, security_key_form_data: object):
        """Signal emitted after the authenticate button is clicked."""

    def reveal_pin_code_entry(self):
        """Reveals the pin code entry."""
        self._pin_code_box_revealer.set_reveal_child(True)

    @property
    def authenticate_button_enabled(self):
        """Returns if the authenticate button is enabled."""
        return self._authenticate_button.enable

    def set_pin_code(self, pin_code: str):
        """Sets the pin code entry."""
        self._pin_code_entry.set_text(pin_code)

    def authenticate_button_click(self):
        """Clicks the authenticate button."""
        self._authenticate_button.clicked()
