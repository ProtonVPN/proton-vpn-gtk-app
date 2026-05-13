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
from proton.vpn.app.gtk.utils.safe_signal_connect import safe_signal_connect
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
        notification_bar: Optional[NotificationBar] = None,
        feature_settings: Optional[FeatureSettings] = None,
        connection_settings: Optional[ConnectionSettings] = None,
        general_settings: Optional[GeneralSettings] = None,
        account_settings: Optional[AccountSettings] = None,
    ):
        super().__init__()
        self.set_name("settings-window")
        self.set_modal(True)
        self.set_title("Settings")
        self.set_default_size(600, 500)

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

        safe_signal_connect(self, "realize", self._build_ui)

        self._controller.settings_watchers.add(self._on_settings_changed)

    def _on_settings_changed(self, settings):
        self._connection_settings.on_settings_changed(settings)
        self._feature_settings.on_settings_changed(settings)
        self._general_settings.on_settings_changed(settings)

    def do_dispose(self):
        """GObject lifecycle hook to release references; may run more
        than once, so cleanup must be idempotent."""
        self._controller.settings_watchers.remove(self._on_settings_changed)
        Gtk.Window.do_dispose(self)  # pylint: disable=no-member

    def _build_ui(self, *_):
        self._account_settings.build_ui()
        self._connection_settings.build_ui()
        self._feature_settings.build_ui()
        self._general_settings.build_ui()

        safe_signal_connect(
            self._feature_settings,
            "netshield-setting-changed",
            self._connection_settings.custom_dns.on_netshield_setting_changed
        )
        safe_signal_connect(
            self._connection_settings.custom_dns,
            "custom-dns-setting-changed",
            self._feature_settings.on_custom_dns_setting_changed
        )

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

        self.content_container.append(self._account_settings)
        self.content_container.append(self._feature_settings)
        self.content_container.append(self._connection_settings)
        self.content_container.append(self._general_settings)

        viewport = Gtk.Viewport()
        viewport.add_css_class("viewport-frame")
        viewport.set_child(self.content_container)

        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_propagate_natural_height(True)
        scrolled_window.set_min_content_height(300)
        scrolled_window.set_min_content_width(400)
        scrolled_window.set_child(viewport)

        self.main_container.append(self._notification_bar)
        self.main_container.append(scrolled_window)

        self.set_child(self.main_container)
