"""
This module defines the widget used to display the 2FA methods

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
from typing import Optional
from gi.repository import Gtk, GObject

from proton.vpn import logging

from proton.vpn.app.gtk.controller import Controller
from proton.vpn.app.gtk.utils.safe_signal_connect import safe_signal_connect
from proton.vpn.app.gtk.widgets.login.logo import TwoFactorAuthProtonVPNLogo
from proton.vpn.app.gtk.widgets.main.notifications import Notifications
from proton.vpn.app.gtk.widgets.main.loading_widget import OverlayWidget
from proton.vpn.app.gtk.widgets.login.two_factor_auth.two_factor_auth_stack import\
    TwoFactorAuthStack

logger = logging.getLogger(__name__)


class TwoFactorAuthWidget(Gtk.Box):
    """Widget used to display the 2FA methods."""
    TWO_FACTOR_AUTH_LABEL = "Two-factor authentication"

    def __init__(
        self,
        controller: Controller,
        notifications: Notifications,
        overlay_widget: OverlayWidget,
        two_factor_auth_stack: Optional[TwoFactorAuthStack] = None
    ):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        self.set_name("two-factor-auth-widget")

        self._two_factor_auth_title = Gtk.Label(label=self.TWO_FACTOR_AUTH_LABEL)
        self._two_factor_auth_title.set_halign(Gtk.Align.CENTER)
        self._two_factor_auth_title.add_css_class("two-factor-auth-stack-title")

        self.two_factor_auth_stack = two_factor_auth_stack \
            or TwoFactorAuthStack(controller, notifications, overlay_widget)

        self.stack_switch = Gtk.StackSwitcher()
        self.stack_switch.set_hexpand(True)
        self.stack_switch.set_name("stack-switch")
        self.stack_switch.set_halign(Gtk.Align.FILL)
        self.stack_switch.set_valign(Gtk.Align.CENTER)

        self.stack_switch.set_stack(self.two_factor_auth_stack)

        # Ensure the children of the stack switcher fill the width of the stack switcher
        child = self.stack_switch.get_first_child()
        while child:
            child.set_hexpand(True)
            child.set_halign(Gtk.Align.FILL)
            child = child.get_next_sibling()

        self.append(TwoFactorAuthProtonVPNLogo())
        self.append(self._two_factor_auth_title)
        self.append(self.stack_switch)
        self.append(self.two_factor_auth_stack)

        safe_signal_connect(
            self.two_factor_auth_stack,
            "two-factor-auth-successful",
            self._on_two_factor_auth_successful
        )
        safe_signal_connect(
            self.two_factor_auth_stack,
            "two-factor-auth-cancelled",
            self._on_two_factor_auth_cancelled
        )

    def _on_two_factor_auth_successful(self, _):
        self.emit("two-factor-auth-successful")

    def _on_two_factor_auth_cancelled(self, _):
        self.emit("two-factor-auth-cancelled")

    def reset(self):
        """Resets the widget to its initial state."""
        self.two_factor_auth_stack.reset()

    @GObject.Signal
    def two_factor_auth_successful(self):
        """Signal emitted after a successful 2FA."""

    @GObject.Signal
    def two_factor_auth_cancelled(self):
        """Signal emitted after 2FA was cancelled by the user."""
