"""
This module defines the login widget, used to authenticate the user.


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
from typing import Protocol, Optional

from gi.repository import GObject

from proton.vpn import logging

from proton.vpn.app.gtk import Gtk
from proton.vpn.app.gtk.controller import Controller
from proton.vpn.app.gtk.utils.safe_signal_connect import safe_signal_connect
from proton.vpn.app.gtk.widgets.login.login_form import LoginForm
from proton.vpn.app.gtk.widgets.login.two_factor_auth import TwoFactorAuthWidget
from proton.vpn.app.gtk.widgets.main.loading_widget import OverlayWidget
from proton.vpn.app.gtk.widgets.main.notifications import Notifications

logger = logging.getLogger(__name__)


class ResettableWidget(Protocol):  # pylint: disable=too-few-public-methods
    """Protocol for widgets that can be reset."""

    def reset(self):
        """Resets the widget to its initial state."""


class LoginStack(Gtk.Stack):
    """Widget used to authenticate the user.

    It inherits from Gtk.Stack and contains 2 widgets stacked on top of the
    other: the LoginForm and the TwoFactorAuthForm. By default, the LoginForm
    widget is shown. Once the user introduces the right username and password
    (and 2FA is enabled) then the TwoFactorAuthForm widget is displayed instead.
    """
    def __init__(
        self, controller: Controller,
        notifications: Notifications, overlay_widget: OverlayWidget
    ):
        super().__init__()

        self._notifications = notifications

        self.set_name("login-stack")
        self._controller = controller
        self.active_widget: Optional[ResettableWidget] = None

        self.login_form = LoginForm(controller, notifications, overlay_widget)
        self.add_named(self.login_form, "login_form")

        self.two_factor_auth_widget = TwoFactorAuthWidget(
            controller, notifications, overlay_widget
        )
        self.add_named(self.two_factor_auth_widget, "2fa_form")

        safe_signal_connect(
            self.login_form,
            "user-authenticated",
            self._on_user_authenticated
        )
        self.display_form(self.login_form)

        safe_signal_connect(
            self.two_factor_auth_widget,
            "two-factor-auth-successful",
            self._on_two_factor_auth_successful
        )

        safe_signal_connect(
            self.two_factor_auth_widget,
            "two-factor-auth-cancelled",
            self._on_two_factor_auth_cancelled
        )

    def _on_user_authenticated(self, _, two_factor_auth_required: bool):
        if not two_factor_auth_required:
            self._signal_user_logged_in()
        else:
            self.display_form(self.two_factor_auth_widget)

    def _on_two_factor_auth_successful(self, _):
        self._signal_user_logged_in()

    def _on_two_factor_auth_cancelled(self, _):
        self.display_form(self.login_form)

    @GObject.Signal
    def user_logged_in(self):
        """Signal emitted after a successful login."""

    def _signal_user_logged_in(self):
        self.emit("user-logged-in")

    def display_form(self, widget: ResettableWidget):
        """
        Displays the specified form to the user. That is, either the login
        form (user/password) or the 2FA form.
        :param widget: The widget to be displayed to the user.
        """
        widget.reset()
        self.active_widget = widget
        self.set_visible_child(widget)

    def reset(self):
        """Resets the widget to its initial state."""
        self.display_form(self.login_form)
