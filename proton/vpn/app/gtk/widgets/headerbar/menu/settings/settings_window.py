"""
Settings window module.


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
from __future__ import annotations
from typing import TYPE_CHECKING, Optional

from gi.repository import Gtk
from proton.vpn.app.gtk.controller import Controller
from proton.vpn.app.gtk.widgets.main.notification_bar import NotificationBar
from proton.vpn.app.gtk.widgets.headerbar.menu.settings.account_settings import \
    AccountSettings
from proton.vpn.app.gtk.widgets.headerbar.menu.settings.connection_settings import \
    ConnectionSettings
from proton.vpn.app.gtk.widgets.headerbar.menu.settings.feature_settings import \
    FeatureSettings
from proton.vpn.app.gtk.widgets.headerbar.menu.settings.general_settings import \
    GeneralSettings
from proton.vpn.app.gtk.widgets.headerbar.menu.settings.common import \
    RECONNECT_MESSAGE

if TYPE_CHECKING:
    from proton.vpn.app.gtk.widgets.main.tray_indicator import TrayIndicator


class SettingsWindow(Gtk.Window):  # pylint: disable=too-many-instance-attributes
    """Main settings window."""
    def __init__(  # pylint: disable=too-many-arguments
        self,
        controller: Controller,
        tray_indicator: Optional["TrayIndicator"] = None,
        notification_bar: NotificationBar = None,
        feature_settings: FeatureSettings = None,
        connection_settings: ConnectionSettings = None,
        general_settings: GeneralSettings = None,
        account_settings: AccountSettings = None,
    ):
        super().__init__(type=Gtk.WindowType.TOPLEVEL)
        self.set_modal(True)
        self.set_title("Settings")
        self.set_default_size(600, 500)
        # Set position is set to center on parent so that we prevent it from
        # spawning somewhere else randomly.
        self.set_position(Gtk.WindowPosition.CENTER_ON_PARENT)

        self._controller = controller
        self._notification_bar = notification_bar or NotificationBar()

        self._account_settings = account_settings or AccountSettings(self._controller)
        self._feature_settings = feature_settings or FeatureSettings(
            self._controller, self
        )
        self._connection_settings = connection_settings or ConnectionSettings(
            self._controller, self
        )
        self._general_settings = general_settings or GeneralSettings(
            self._controller, tray_indicator
        )

        self._create_elastic_window()

        self.connect("realize", self._build_ui)

    def _build_ui(self, *_):
        self._account_settings.build_ui()
        self._connection_settings.build_ui()
        self._feature_settings.build_ui()
        self._general_settings.build_ui()

        if self._controller.feature_flags.get("CustomDNS"):
            self._feature_settings \
                .connect(
                    "netshield-setting-changed",
                    self._connection_settings.custom_dns.on_netshield_setting_changed
                )
            self._connection_settings.custom_dns \
                .connect(
                    "custom-dns-setting-changed",
                    self._feature_settings.on_custom_dns_setting_changed
                )

        self.show_all()

    def notify_user_with_reconnect_message(
        self, force_notify: bool = False, only_notify_on_active_connection: bool = False
    ):
        """Notify user with a reconnect message when connected
        and when the settings changes require a starting a new connection.
        """
        is_connection_active = self._controller.is_connection_active  # noqa: E501 # pylint: disable=line-too-long # nosemgrep: python.lang.maintainability.is-function-without-parentheses.is-function-without-parentheses
        if (
            (
                is_connection_active
                and not self._controller.current_connection.are_feature_updates_applied_when_active
            ) or (
                is_connection_active
                and only_notify_on_active_connection
            ) or force_notify
        ):
            self._notification_bar.show_info_message(f"{RECONNECT_MESSAGE}")

    def _create_elastic_window(self):
        """This allows for the content to be always centered and expand or contract
        based on window size.

        The reason we use two containers is mainly due to the notification bar, as this
        way the notification will span across the entire window while only the
        settings will be centered.
        """
        self.main_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.content_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

        self.content_container.pack_start(self._account_settings, False, False, 0)
        self.content_container.pack_start(self._feature_settings, False, False, 0)
        self.content_container.pack_start(self._connection_settings, False, False, 0)
        self.content_container.pack_start(self._general_settings, False, False, 0)

        viewport = Gtk.Viewport()
        viewport.get_style_context().add_class("viewport-frame")
        viewport.add(self.content_container)

        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_propagate_natural_height(True)
        scrolled_window.set_min_content_height(300)
        scrolled_window.set_min_content_width(400)
        scrolled_window.add(viewport)

        self.main_container.pack_start(self._notification_bar, False, False, 0)
        self.main_container.pack_start(scrolled_window, False, False, 0)

        self.add(self.main_container)
