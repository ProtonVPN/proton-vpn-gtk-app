"""
Account settings module.


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
from gi.repository import Gtk, Gdk
from proton.vpn.app.gtk.controller import Controller
from proton.vpn.app.gtk.widgets.headerbar.menu.settings.common import (
    BaseCategoryContainer, CustomButton
)


class AccountSettings(BaseCategoryContainer):  # pylint: disable=too-many-instance-attributes
    """Account settings are grouped under this class."""
    CATEGORY_NAME = "Account"
    MANAGE_ACCOUNT_URL = "https://account.protonvpn.com/account"

    def __init__(self, controller: Controller):
        super().__init__(self.CATEGORY_NAME)
        self._controller = controller

    def build_ui(self):
        """Builds the UI, invoking all necessary methods that are
        under this category."""
        self.pack_start(CustomButton(
            title=self._controller.account_name,
            description=f"VPN plan: {self._controller.account_data.plan_title or 'Free'}",
            button_label="Manage Account",
            on_click_callback=self._on_click_manage_account_button,
            bold_title=True
        ), False, False, 0)

    def _on_click_manage_account_button(self, *_):
        Gtk.show_uri_on_window(
            None,
            self.MANAGE_ACCOUNT_URL,
            Gdk.CURRENT_TIME
        )
