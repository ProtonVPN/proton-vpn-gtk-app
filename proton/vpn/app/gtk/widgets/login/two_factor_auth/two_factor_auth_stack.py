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
from gi.repository import GObject, Gtk

from proton.vpn import logging
from proton.vpn.app.gtk.controller import Controller
from proton.vpn.app.gtk.widgets.main.notifications import Notifications
from proton.vpn.app.gtk.widgets.main.loading_widget import OverlayWidget
from proton.vpn.app.gtk.widgets.login.two_factor_auth.authenticator_app_form \
    import AuthenticatorAppForm
from proton.vpn.app.gtk.widgets.login.two_factor_auth.security_key_form \
    import SecurityKeyForm

logger = logging.getLogger(__name__)


class TwoFactorAuthStack(Gtk.Stack):
    """Stack used to display the 2FA methods."""
    AUTHENTICATOR_APP_FORM_TITLE = "Authenticator app"
    SECURITY_KEY_FORM_TITLE = "Security key"

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

        self.authenticator_app_form = authenticator_app_form or AuthenticatorAppForm(
            controller, notifications, overlay_widget
        )
        self.add_titled(
            self.authenticator_app_form, "authenticator_app_form", self.AUTHENTICATOR_APP_FORM_TITLE
        )
        self.authenticator_app_form.connect(
            "two-factor-auth-successful",
            self._on_two_factor_auth_successful
        )
        self.authenticator_app_form.connect(
            "two-factor-auth-cancelled", self._on_two_factor_auth_cancelled
        )

        # Only show the security key form if environment variable is set and FIDO2 is available,
        # otherwise it will be hidden by default (shows only authenticator app form).
        # The environment variable should be removed once we fully deploy this feature,
        # unless we implement a logic that hides it
        # if a user doesn't have a security key configured.
        if controller.fido2_available and controller.security_key_env_variable_set:
            self.security_key_form = security_key_form or SecurityKeyForm(
                controller, notifications, overlay_widget
            )
            self.security_key_form.connect(
                "two-factor-auth-successful", self._on_two_factor_auth_successful
            )
            self.security_key_form.connect(
                "two-factor-auth-cancelled", self._on_two_factor_auth_cancelled
            )
            self.add_titled(
                self.security_key_form, "security_key_form", self.SECURITY_KEY_FORM_TITLE
            )

    def display_widget(self, widget: Union[AuthenticatorAppForm, SecurityKeyForm]):
        """
        Displays the specified form to the user.
        """
        self.active_widget = widget
        self.set_visible_child(widget)
        widget.reset()

    def reset(self):
        """Resets the widget to its initial state."""
        self._notifications.hide_message()
        self.display_widget(self.authenticator_app_form)

    def _on_two_factor_auth_successful(self, _):
        self.emit("two-factor-auth-successful")

    def _on_two_factor_auth_cancelled(self, _):
        self.emit("two-factor-auth-cancelled")

    @GObject.Signal
    def two_factor_auth_successful(self):
        """Signal emitted after a successful 2FA."""

    @GObject.Signal
    def two_factor_auth_cancelled(self):
        """Signal emitted after 2FA was cancelled by the user."""
