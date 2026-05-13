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
from typing import TYPE_CHECKING, Optional

from gi.repository import GObject

from proton.vpn.app.gtk.controller import Controller
from proton.vpn.app.gtk import Gtk
from proton.vpn import logging
from proton.vpn.app.gtk.utils.safe_signal_connect import safe_signal_connect
from proton.vpn.app.gtk.widgets.login.login_stack import LoginStack
from proton.vpn.app.gtk.widgets.login.disable_killswitch import DisableKillSwitchWidget
from proton.vpn.app.gtk.widgets.main.notifications import Notifications
from proton.vpn.app.gtk.widgets.main.loading_widget import OverlayWidget
from proton.vpn.connection.enum import KillSwitchSetting as KillSwitchSettingEnum

if TYPE_CHECKING:
    from proton.vpn.app.gtk.app import MainWindow


logger = logging.getLogger(__name__)


#  pylint: disable=too-many-arguments
class LoginWidget(Gtk.Box):
    """Container widget that holds both
    login UI and also a revealer to display
    in the case the user is logged out and permanent
    kill switch is enabled.
    """
    def __init__(
        self,
        controller: Controller,
        notifications: Notifications,
        overlay_widget: OverlayWidget,
        main_window: "MainWindow",
        login_stack: Optional["LoginStack"] = None,
        disable_killswitch_widget: Optional[DisableKillSwitchWidget] = None
    ):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)

        self.set_name("login-widget")

        self._controller = controller

        self.login_stack = login_stack or LoginStack(
            self._controller, notifications, overlay_widget
        )
        safe_signal_connect(self.login_stack, "user-logged-in", self._on_user_logged_in)

        self.disable_killswitch = disable_killswitch_widget or DisableKillSwitchWidget(
            main_window
        )
        safe_signal_connect(
            self.disable_killswitch,
            "disable-killswitch",
            self._on_disable_killswitch
        )

        self.append(self.login_stack)
        self.append(self.disable_killswitch)

    @GObject.Signal
    def user_logged_in(self):
        """Signal emitted after a successful login."""

    def _on_user_logged_in(self, _: "LoginStack"):
        self.emit("user-logged-in")

    def reset(self):
        """Proxy method to reset the widget to its initial state."""
        is_ks_permanent = self._controller.get_settings()\
            .killswitch == KillSwitchSettingEnum.PERMANENT
        self.disable_killswitch.set_reveal_child(is_ks_permanent)
        self.login_stack.login_form.set_property("sensitive", not is_ks_permanent)
        self.login_stack.reset()

    def _on_disable_killswitch(self, _):
        settings = self._controller.get_settings()
        settings.killswitch = KillSwitchSettingEnum.OFF
        self._controller.save_settings(settings)

        self.disable_killswitch.set_reveal_child(False)
        self.login_stack.login_form.set_property("sensitive", True)
