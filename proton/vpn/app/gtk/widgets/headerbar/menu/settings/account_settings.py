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
from gi.repository import Gio
from proton.vpn import logging
from proton.vpn.app.gtk.controller import Controller
from proton.vpn.app.gtk.translator import C_
from proton.vpn.app.gtk.widgets.main.notification_bar import NotificationBar
from proton.vpn.app.gtk.widgets.headerbar.menu.settings.common import (
    BaseCategoryContainer, CustomButton
)

logger = logging.getLogger(__name__)


class AccountSettings(BaseCategoryContainer):  # pylint: disable=too-many-instance-attributes
    """Account settings are grouped under this class."""
    CATEGORY_NAME = C_("title", "Account")
    MANAGE_ACCOUNT_URL = "https://account.protonvpn.com/account"
    REFRESH_INFO_MESSAGE = C_("message", "Account info refreshed, restart the app to see changes")
    REFRESH_ERROR_MESSAGE = C_("error",
                               "Account info refresh failed, check your connection and try again")

    def __init__(self, controller: Controller,
                 notification_bar: NotificationBar
                 ):
        super().__init__(self.CATEGORY_NAME)
        self._controller = controller
        self._notification_bar = notification_bar
        self._refreshing = False  # only allow one request at a time
        self._account_row: CustomButton

    def build_ui(self):
        """Builds the UI, invoking all necessary methods that are
        under this category."""
        self._account_row = CustomButton(
            title=self._controller.account_name,
            description=C_("label", "VPN plan: {plan}").format(
                plan=self._controller.account_data.plan_title or C_("label", "Free")
            ),
            button_label=C_("button", "Manage Account"),
            on_click_callback=self._on_click_manage_account_button,
            bold_title=True,
            extra_button=CustomButton.build_icon_button(
                "view-refresh-symbolic",
                C_("tooltip", "Refresh account details"),
                self._on_click_refresh_vpn_info
            )
        )
        self.append(self._account_row)

    def _on_click_manage_account_button(self, *_):
        Gio.AppInfo.launch_default_for_uri(self.MANAGE_ACCOUNT_URL, None)

    def _on_click_refresh_vpn_info(self, *_):
        if self._refreshing:
            return
        self._refreshing = True
        self._controller.refresh_vpn_info(
            on_done=self._on_vpn_info_refreshed,
            on_error=self._on_vpn_info_failed,
        )

    def _on_vpn_info_refreshed(self, vpninfo):
        self._refreshing = False
        logger.info("VPN info refreshed: %r", vpninfo)
        self._notification_bar.show_info_message(self.REFRESH_INFO_MESSAGE)
        # Refresh the displayed plan name
        self._account_row.description.set_text(
            C_("label", "VPN plan: {plan}").format(
                plan=self._controller.account_data.plan_title)
        )

    def _on_vpn_info_failed(self, error):
        self._refreshing = False
        logger.warning("VPN info refresh failed: %r", error)
        self._notification_bar.show_error_message(self.REFRESH_ERROR_MESSAGE)
