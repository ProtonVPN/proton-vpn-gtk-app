"""
This module defines the two factor authentication stack, used to contain
the different 2FA methods.


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
from typing import Union
from concurrent.futures import Future
from gi.repository import GLib, GObject, Gtk

from proton.vpn import logging
from proton.vpn.app.gtk.controller import Controller
from proton.vpn.app.gtk.widgets.main.notifications import Notifications
from proton.vpn.app.gtk.widgets.main.loading_widget import OverlayWidget, DefaultLoadingWidget
from proton.vpn.app.gtk.widgets.login.two_factor_auth.authenticator_app_form \
    import AuthenticatorAppForm
from proton.vpn.app.gtk.widgets.login.two_factor_auth.security_key_form \
    import SecurityKeyForm, SecurityKeyFormData

from proton.vpn.session.exceptions import \
    SecurityKeyError, SecurityKeyNotFoundError, InvalidSecurityKeyError, \
    SecurityKeyTimeoutError, Fido2NotSupportedError

logger = logging.getLogger(__name__)


class TwoFactorAuthStack(Gtk.Stack):
    """Stack used to display the 2FA methods."""
    AUTHENTICATOR_APP_FORM_TITLE = "Authenticator app"
    SECURITY_KEY_FORM_TITLE = "Security key"

    LOGGING_IN_MESSAGE = "Signing in..."
    SESSION_EXPIRED_MESSAGE = "Session expired. Please sign in again."
    INCORRECT_TWOFA_CODE_MESSAGE = "Incorrect 2FA code."
    PHYSICAL_VERIFICATION_MESSAGE = "If your security key has a button or a gold disc, tap it now."

    SECURITY_KEY_NOT_FOUND_MESSAGE = "Two-factor authentication failed. No security key detected."
    INVALID_SECURITY_KEY_MESSAGE = "Two-factor authentication failed. The security key you used " \
        "isn’t linked to your Proton Account."
    FIDO2_NOT_SUPPORTED_MESSAGE = "Two-factor authentication failed. Security key 2FA is not " \
        "enabled for your account."
    GENERIC_ERROR_MESSAGE = "An unknown error occurred"

    def __init__(  # pylint: disable=too-many-arguments
        self,
        controller: Controller,
        notifications: Notifications,
        overlay_widget: OverlayWidget,
        authenticator_app_form: AuthenticatorAppForm = None,
        security_key_form: SecurityKeyForm = None
    ):
        super().__init__()

        self.set_name("two-factor-auth-stack")
        self._controller = controller
        self._notifications = notifications
        self._overlay_widget = overlay_widget
        self.active_widget = None
        self.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        self.security_key_form = None

        self.authenticator_app_form = authenticator_app_form or AuthenticatorAppForm()
        self.add_titled(
            self.authenticator_app_form, "authenticator_app_form", self.AUTHENTICATOR_APP_FORM_TITLE
        )
        self.authenticator_app_form.connect(
            "authenticate-button-clicked", self._on_authenticate_with_authenticator_app
        )

        # Only show the security key form if environment variable is set and FIDO2 is available,
        # otherwise it will be hidden by default (shows only authenticator app form).
        # The environment variable should be removed once we fully deploy this feature,
        # unless we implement a logic that hides it
        # if a user doesn't have a security key configured.
        if controller.fido2_available and controller.security_key_env_variable_set:
            self.security_key_form = security_key_form or SecurityKeyForm()
            self.add_titled(
                self.security_key_form, "security_key_form", self.SECURITY_KEY_FORM_TITLE
            )
            self.security_key_form.connect(
                "authenticate-button-clicked", self._on_authenticate_with_security_key
            )

    def display_widget(self, widget: Union[AuthenticatorAppForm, SecurityKeyForm]):
        """
        Displays the specified form to the user.
        """
        self.active_widget = widget
        self.set_visible_child(widget)
        widget.reset()

    def _on_authenticate_with_security_key(self, _, security_key_form_data: SecurityKeyFormData):
        # Form data is logged only for testing purposes, once implemented
        # remove the form data from the logger message.
        logger.info(
            f"Clicked on authenticate via security key {security_key_form_data}",
            category="UI", subcategory="LOGIN-2FA", event="CLICK"
        )
        self._show_loading_message(self.PHYSICAL_VERIFICATION_MESSAGE)

        future = self._controller.generate_2fa_fido2_assertion()
        future.add_done_callback(
            lambda future: GLib.idle_add(self._on_2fa_fido2_assertion, future)
        )

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
        except (SecurityKeyError, SecurityKeyTimeoutError) as excp:
            logger.exception(str(excp), category="APP", subcategory="LOGIN-2FA", event="ERROR")
            msg = self.GENERIC_ERROR_MESSAGE

        if msg:
            self._show_error_message(msg)
            self._overlay_widget.hide()
            return

        self._show_loading_message(self.LOGGING_IN_MESSAGE)

        future = self._controller.submit_2fa_fido2(assertion)
        future.add_done_callback(
            lambda future: GLib.idle_add(self._on_2fa_submission_result, future)
        )

    def _on_authenticate_with_authenticator_app(self, _, authenticator_app_code: str):
        logger.info(
            "Clicked on authenticate via authenticator app",
            category="UI", subcategory="LOGIN-2FA", event="CLICK"
        )
        self._show_loading_message(self.LOGGING_IN_MESSAGE)

        future = self._controller.submit_2fa_code(authenticator_app_code)
        future.add_done_callback(
            lambda future: GLib.idle_add(self._on_2fa_submission_result, future)
        )

    def _on_2fa_submission_result(self, future: Future):
        try:
            result = future.result()
        finally:
            self._hide_loading_message()

        if not result.authenticated:
            self._show_error_message(self.SESSION_EXPIRED_MESSAGE)
            logger.debug(
                self.SESSION_EXPIRED_MESSAGE, category="APP",
                subcategory="LOGIN-2FA", event="RESULT"
            )
            self._signal_session_expired()
        elif result.twofa_required:
            self._show_error_message(self.INCORRECT_TWOFA_CODE_MESSAGE)
            logger.debug(
                self.INCORRECT_TWOFA_CODE_MESSAGE, category="APP",
                subcategory="LOGIN-2FA", event="RESULT"
            )
        else:
            self._signal_two_factor_auth_successful()

    def _show_error_message(self, error: str):
        self._notifications.show_error_message(error)

    def _show_loading_message(self, message: str):
        self._overlay_widget.hide()
        self._overlay_widget.show(DefaultLoadingWidget(message))

    def _hide_loading_message(self):
        self._overlay_widget.hide()

    def reset(self):
        """Resets the widget to its initial state."""
        self._notifications.hide_message()
        self.display_widget(self.authenticator_app_form)

    def _signal_session_expired(self):
        self.emit("session-expired")

    def _signal_two_factor_auth_successful(self):
        self.emit("two-factor-auth-successful")

    @GObject.Signal
    def session_expired(self):
        """Signal emitted when the session expired and the user has to log in again."""

    @GObject.Signal
    def two_factor_auth_successful(self):
        """Signal emitted after a successful 2FA."""
