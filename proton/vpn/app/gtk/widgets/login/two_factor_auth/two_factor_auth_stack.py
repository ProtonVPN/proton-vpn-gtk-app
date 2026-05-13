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
from concurrent.futures import Future
from typing import Union, Optional
from gi.repository import GObject, Gtk

from proton.vpn import logging
from proton.vpn.app.gtk.controller import Controller
from proton.vpn.app.gtk.util import connect_once
from proton.vpn.app.gtk.utils.glib import add_done_callback
from proton.vpn.app.gtk.utils.safe_signal_connect import safe_signal_connect
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
        authenticator_app_form: Optional[AuthenticatorAppForm] = None,
        security_key_form: Optional[SecurityKeyForm] = None
    ):
        super().__init__()

        self.set_name("two-factor-auth-stack")
        self._controller = controller
        self._notifications = notifications
        self._overlay_widget = overlay_widget
        self.active_widget: Optional[Union[AuthenticatorAppForm, SecurityKeyForm]] = None
        self.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        self._pending_logout_future = None

        # SecurityKeyForm
        self.security_key_form = security_key_form or SecurityKeyForm(
            controller, notifications, overlay_widget
        )
        safe_signal_connect(
            self.security_key_form,
            "two-factor-auth-successful",
            self._on_two_factor_auth_successful
        )
        safe_signal_connect(
            self.security_key_form,
            "two-factor-auth-cancelled",
            self._on_two_factor_auth_cancelled
        )

        # AuthenticatorAppForm
        self.authenticator_app_form = authenticator_app_form or AuthenticatorAppForm(
            controller, notifications, overlay_widget
        )
        safe_signal_connect(
            self.authenticator_app_form,
            "two-factor-auth-successful",
            self._on_two_factor_auth_successful
        )
        safe_signal_connect(
            self.authenticator_app_form,
            "two-factor-auth-cancelled",
            self._on_two_factor_auth_cancelled
        )

    def display_widget(self, widget: Union[AuthenticatorAppForm, SecurityKeyForm]):
        """
        Displays the specified form to the user.
        """
        if widget is not self.get_child_by_name("authenticator_app_form") and \
           widget is not self.get_child_by_name("security_key_form"):
            raise ValueError("Invalid widget to display in TwoFactorAuthStack")

        self.active_widget = widget
        self.set_visible_child(widget)
        widget.reset()

    def reset(self):
        """Resets the widget to its initial state."""
        self._notifications.hide_message()

        # Remove all children first
        if self.get_child_by_name("security_key_form"):
            self.remove(self.security_key_form)
        if self.get_child_by_name("authenticator_app_form"):
            self.remove(self.authenticator_app_form)

        if self._controller.fido2_available:
            self.add_titled(
                self.security_key_form,
                "security_key_form",
                self.SECURITY_KEY_FORM_TITLE
            )
            self.add_titled(
                self.authenticator_app_form,
                "authenticator_app_form",
                self.AUTHENTICATOR_APP_FORM_TITLE
            )
            self.display_widget(self.security_key_form)
        else:
            self.add_titled(
                self.authenticator_app_form,
                "authenticator_app_form",
                self.AUTHENTICATOR_APP_FORM_TITLE
            )
            self.display_widget(self.authenticator_app_form)

    def _on_two_factor_auth_successful(self, _):
        self.emit("two-factor-auth-successful")

    def _on_two_factor_auth_cancelled(self, _):
        logger.info(
            "2FA cancelled by user, signing out...",
            category="UI", subcategory="LOGIN-2FA", event="CLICK"
        )
        self._overlay_widget.show_message("Signing out...")
        future = self._controller.logout()
        add_done_callback(future, self._on_logout)

    def _on_logout(self, logout_future: Future):
        self._pending_logout_future = logout_future
        connect_once(
            self._overlay_widget,
            "hide",
            self._on_overlay_hidden_after_logout,
        )
        self._overlay_widget.hide()

    def _on_overlay_hidden_after_logout(self, _overlay_widget: OverlayWidget):
        self._pending_logout_future.result()
        self._pending_logout_future = None
        self.emit("two-factor-auth-cancelled")

    @GObject.Signal
    def two_factor_auth_successful(self):
        """Signal emitted after a successful 2FA."""

    @GObject.Signal
    def two_factor_auth_cancelled(self):
        """Signal emitted after 2FA was cancelled by the user."""
