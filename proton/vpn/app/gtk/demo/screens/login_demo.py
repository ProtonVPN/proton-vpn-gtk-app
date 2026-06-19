"""
Copyright (c) 2026 Proton AG

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


Demo factory for the login widget.
"""
from unittest.mock import MagicMock

from proton.vpn.connection.enum import KillSwitchSetting

from proton.vpn.app.gtk import Gtk
from proton.vpn.app.gtk.demo.registry import register_demo
from proton.vpn.app.gtk.demo.mocks import mock_controller, mock_main_window
from proton.vpn.app.gtk.demo.framing import framed_like_app
from proton.vpn.app.gtk.widgets.login.login_widget import LoginWidget


def _login(
    killswitch: KillSwitchSetting = KillSwitchSetting.OFF,
    fido2_available: bool = False,
    show_2fa: bool = False,
) -> Gtk.Widget:
    controller = mock_controller(killswitch=killswitch)
    # The 2FA stack reads this to decide which form to show: the security-key
    # form when True, the authenticator-app form when False.
    controller.fido2_available = fido2_available

    widget = LoginWidget(
        controller=controller,
        notifications=MagicMock(name="Notifications"),
        overlay_widget=MagicMock(name="OverlayWidget"),
        main_window=mock_main_window(),
    )
    # reset() puts the widget into the state the app initially shows: it reads the
    # kill-switch setting to decide whether to reveal the disable-killswitch
    # banner and whether the login form is sensitive.
    widget.reset()

    if show_2fa:
        # Switch the stack to the 2FA view (as happens after username/password
        # with 2FA enabled). display_form() resets the 2FA widget, which only
        # sets UI state — no controller call or FIDO2 work is triggered.
        stack = widget.login_stack
        stack.display_form(stack.two_factor_auth_widget)

    # The login fills the MainWindow in the app, so frame it to fill the height.
    return framed_like_app(widget, fill_height=True)


@register_demo("login", label="default")
def login_default() -> Gtk.Widget:
    """Login widget in its default state."""
    return _login()


@register_demo("login", label="permanent-killswitch")
def login_permanent_killswitch() -> Gtk.Widget:
    """Login widget with the permanent kill switch active."""
    return _login(killswitch=KillSwitchSetting.PERMANENT)


@register_demo("login", label="2fa-authenticator")
def login_2fa_authenticator() -> Gtk.Widget:
    """Login widget on the 2FA step, authenticator-app variant."""
    return _login(show_2fa=True, fido2_available=False)


@register_demo("login", label="2fa-security-key")
def login_2fa_security_key() -> Gtk.Widget:
    """Login widget on the 2FA step, security-key variant."""
    return _login(show_2fa=True, fido2_available=True)
