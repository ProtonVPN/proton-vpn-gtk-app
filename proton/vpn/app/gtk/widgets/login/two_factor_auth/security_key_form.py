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
import threading
from concurrent.futures import Future
from typing import Optional

from gi.repository import GLib, GObject

from proton.vpn import logging
from proton.vpn.session.exceptions import \
    SecurityKeyError, SecurityKeyNotFoundError, InvalidSecurityKeyError, \
    SecurityKeyPINNotSetError, SecurityKeyPINInvalidError, Fido2NotSupportedError

from proton.vpn.app.gtk import Gtk
from proton.vpn.app.gtk.controller import Controller
from proton.vpn.app.gtk.utils.safe_signal_connect import safe_signal_connect
from proton.vpn.app.gtk.widgets.login.logo import SecurityKeyLogo
from proton.vpn.app.gtk.widgets.headerbar.menu.settings.common import SettingDescription
from proton.vpn.app.gtk.widgets.login.password_entry import PasswordEntry
from proton.vpn.app.gtk.widgets.login.two_factor_auth.authenticate_button import AuthenticateButton
from proton.vpn.app.gtk.widgets.main.loading_widget import OverlayWidget
from proton.vpn.app.gtk.widgets.main.notifications import Notifications

logger = logging.getLogger(__name__)

LEARN_MORE_LINK = '<a href="https://protonvpn.com/support/#">Learn more</a>'


class SecurityKeyForm(Gtk.Box):  # pylint: disable=R0902
    """
    Implements the UI for HOTP authentication.
    Once the HOTP code is authenticated,
    it emits the `hotp-auth-successful` signal.
    """
    DESCRIPTION_LABEL = "Insert the U2F or FIDO key linked to your Proton Account. " \
        + LEARN_MORE_LINK
    PIN_CODE_LABEL = "PIN code"

    MULTIPLE_SECURITY_KEYS_FOUND = "Multiple security keys were found. Tap one to select it."
    PHYSICAL_VERIFICATION_MESSAGE = "If your security key has a button or a gold disc, tap it now."
    SECURITY_KEY_NOT_FOUND_MESSAGE = "Two-factor authentication failed: No security key detected"
    INVALID_SECURITY_KEY_MESSAGE = "Two-factor authentication failed: The security key you used " \
        "is not linked to your Proton Account."
    FIDO2_NOT_SUPPORTED_MESSAGE = "Two-factor authentication failed. Security key 2FA is not " \
        "enabled for your account."
    SECURITY_KEY_PIN_NOT_SET_MESSAGE = "Two-factor authentication failed: " \
        "Your security key has no PIN set"
    SECURITY_KEY_PIN_INVALID_MESSAGE = "Two-factor authentication failed: Incorrect PIN"
    GENERIC_ERROR_MESSAGE = "An unknown error occurred"
    LOGGING_IN_MESSAGE = "Signing in..."

    def __init__(
            self,
            controller: Controller,
            notifications: Notifications,
            overlay_widget: OverlayWidget,
            authenticate_button: Optional[AuthenticateButton] = None
    ):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=15)

        self.set_name("security-device-form")

        self._controller = controller
        self._notifications = notifications
        self._overlay_widget = overlay_widget

        self._authenticate_button = authenticate_button or AuthenticateButton()
        safe_signal_connect(
            self._authenticate_button, "clicked", self._on_authenticate_button_clicked
        )

        self._cancel_button = Gtk.Button(label="Cancel")
        self._cancel_button.add_css_class("danger")
        safe_signal_connect(self._cancel_button, "clicked", self._on_cancel_button_clicked)

        self._instruction_label = SettingDescription(self.DESCRIPTION_LABEL)
        self._instruction_label.remove_css_class("dim-label")
        self._instruction_label.set_wrap(True)

        self._pin_code_label = Gtk.Label(label=self.PIN_CODE_LABEL)
        self._pin_code_label.set_halign(Gtk.Align.START)

        self._pin_code_entry = PasswordEntry()
        self._pin_code_entry.set_input_purpose(Gtk.InputPurpose.FREE_FORM)
        safe_signal_connect(
            self._pin_code_entry, "changed", self._on_pin_code_entry_changed
        )
        safe_signal_connect(
            self._pin_code_entry, "activate", self._on_authenticate_button_clicked
        )

        self._requesting_pin: Optional[threading.Event] = None
        self._cancel_assertion: Optional[threading.Event] = None

        # Box is used to group the pin code label and the pin code entry.
        self._pin_code_box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL, spacing=10
        )
        self._pin_code_box.append(self._pin_code_label)
        self._pin_code_box.append(self._pin_code_entry)

        self._pin_code_box_revealer = Gtk.Revealer()
        self._pin_code_box_revealer.set_name("pin-code-box-revealer")
        self._pin_code_box_revealer.set_child(self._pin_code_box)
        safe_signal_connect(
            self._pin_code_box_revealer,
            "notify::reveal-child", self._on_pin_code_box_revealer_notify_reveal_child
        )

        # Box is used to group the pin code box revealer and the authenticate button.
        self._authenticate_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self._authenticate_box.set_vexpand(True)
        self._authenticate_box.set_valign(Gtk.Align.END)
        self._authenticate_box.append(self._pin_code_box_revealer)
        self._authenticate_box.append(self._authenticate_button)
        self._authenticate_box.append(self._cancel_button)
        self.append(self._instruction_label)
        self.append(SecurityKeyLogo())
        self.append(self._authenticate_box)

    @GObject.Signal
    def two_factor_auth_cancelled(self):
        """Signal emitted after the user cancelled 2FA"""

    @GObject.Signal
    def two_factor_auth_successful(self):
        """Signal emitted after a successful 2FA."""

    def _on_authenticate_button_clicked(self, _):
        """Called when the authenticate button is clicked."""
        self._authenticate_button.set_sensitive(False)
        if self._requesting_pin:
            # Authenticate button clicked again after PIN request
            self._requesting_pin.set()
        else:
            self._cancel_assertion = threading.Event()
            logger.info(
                "Clicked on authenticate via security key",
                category="UI", subcategory="LOGIN-2FA", event="CLICK"
            )
            future = self._controller.generate_2fa_fido2_assertion(
                user_interaction=self,
                cancel_assertion=self._cancel_assertion
            )
            future.add_done_callback(
                lambda future: GLib.idle_add(self._on_2fa_fido2_assertion,
                                             future)
            )

    def _on_cancel_button_clicked(self, _):
        if self._cancel_assertion:
            self._cancel_assertion.set()
        self.emit("two-factor-auth-cancelled")
        self.reset()

    def _on_2fa_fido2_assertion(self, future: Future):
        msg = None

        try:
            assertion = future.result()
        except Fido2NotSupportedError:
            msg = self.FIDO2_NOT_SUPPORTED_MESSAGE
        except SecurityKeyNotFoundError:
            msg = self.SECURITY_KEY_NOT_FOUND_MESSAGE
        except InvalidSecurityKeyError:
            msg = self.INVALID_SECURITY_KEY_MESSAGE
        except SecurityKeyPINNotSetError:
            msg = self.SECURITY_KEY_PIN_NOT_SET_MESSAGE
        except SecurityKeyPINInvalidError:
            msg = self.SECURITY_KEY_PIN_INVALID_MESSAGE
        except (SecurityKeyError) as excp:
            logger.exception(str(excp), category="APP", subcategory="LOGIN-2FA", event="ERROR")
            msg = self.GENERIC_ERROR_MESSAGE

        self.reset()

        if msg:
            self._notifications.show_error_message(msg)
            logger.warning(msg, category="APP", subcategory="LOGIN-2FA", event="ERROR")
            self._overlay_widget.hide()
            return

        self._overlay_widget.show_message(self.LOGGING_IN_MESSAGE)

        future = self._controller.submit_2fa_fido2(assertion)
        future.add_done_callback(
            lambda future: GLib.idle_add(self._on_2fa_fido2_submission_result, future)
        )

    def _on_2fa_fido2_submission_result(self, future: Future):
        try:
            result = future.result()
        finally:
            self._overlay_widget.hide()

        if result.success:
            self.emit("two-factor-auth-successful")
        else:
            self._notifications.show_error_message(self.GENERIC_ERROR_MESSAGE)

    def _on_pin_code_box_revealer_notify_reveal_child(self, *_):
        """Called when the pin code box revealer is notified of a reveal child change."""
        self._authenticate_button.enable = len(self._pin_code_entry.get_text()) > 0

    def _on_pin_code_entry_changed(self, _):
        """Toggles pin code entry state based on pin code length."""
        self._authenticate_button.enable = len(self._pin_code_entry.get_text()) > 0

    def reset(self):
        """Resets the widget to its initial state."""
        self._pin_code_box_revealer.set_reveal_child(False)
        self._pin_code_entry.set_text("")
        self._authenticate_button.enable = True
        self._requesting_pin = None
        self._authenticate_button.set_sensitive(True)
        self._authenticate_button.grab_focus()

    def reveal_pin_code_entry(self):
        """Reveals the pin code entry."""
        self._pin_code_box_revealer.set_reveal_child(True)
        self._pin_code_entry.grab_focus()

    @property
    def authenticate_button_enabled(self):
        """Returns if the authenticate button is enabled."""
        return self._authenticate_button.enable

    def set_pin_code(self, pin_code: str):
        """Sets the pin code entry."""
        self._pin_code_entry.set_text(pin_code)

    def authenticate_button_click(self):
        """Clicks the authenticate button."""
        self._authenticate_button.emit("clicked")

    def request_key_selection(self):
        """Called when multiple keys are found and the user needs to select one
        by touching it."""
        GLib.idle_add(self._overlay_widget.show_message, self.MULTIPLE_SECURITY_KEYS_FOUND)

    def prompt_up(self) -> None:
        """Called when the FIDO2 client checks for user presence."""
        GLib.idle_add(self._overlay_widget.show_message, self.PHYSICAL_VERIFICATION_MESSAGE)

    def request_pin(self, *_args, **_kwargs) -> Optional[str]:
        """
        Called if the FIDO2 client requires a PIN.
        :returns: the PIN the user typed or None/empty to cancel.
        """
        self._requesting_pin = threading.Event()
        GLib.idle_add(self.reveal_pin_code_entry)
        GLib.idle_add(self._overlay_widget.hide)
        self._requesting_pin.wait()
        self._requesting_pin = None
        return self._pin_code_entry.get_text()

    def request_uv(self, *_args, **_kwargs) -> bool:
        """
        Called when the FIDO2 client is about to request UV (user verification) from the user.
        :returns: True if allowed, or False to cancel.
        """
        return True
