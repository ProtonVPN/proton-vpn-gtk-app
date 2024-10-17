"""
General settings module.


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
from typing import TYPE_CHECKING, Optional, List
from gi.repository import Gtk, Gdk
from proton.vpn import logging
from proton.vpn.app.gtk.controller import Controller
from proton.vpn.app.gtk.widgets.headerbar.menu.settings.common import (
    BaseCategoryContainer, ToggleWidget, EntryWidget, get_setting,
    save_setting
)
from proton.vpn.app.gtk.widgets.headerbar.menu.settings.early_access import \
    EarlyAccessWidget
if TYPE_CHECKING:
    from proton.vpn.app.gtk.widgets.main.tray_indicator import TrayIndicator

logger = logging.getLogger(__name__)


class TrayPinnedServersWidget(EntryWidget):
    """Custom widget that holds the pinned servers to tray setting."""
    TRAY_PINNED_SERVERS_LABEL = "Pinned tray connections"
    TRAY_PINNED_SERVERS_DESCRIPTION = "Access preferred connections from system tray."\
        " Enter country or server codes, separated by commas, to quickly connect "\
        "(e.g.: NL#42, JP, US, IT#01)."
    SETTING_NAME = "app_configuration.tray_pinned_servers"

    def __init__(self, controller: Controller, tray_indicator: "TrayIndicator" = None):
        super().__init__(
            controller=controller,
            title=self.TRAY_PINNED_SERVERS_LABEL,
            description=self.TRAY_PINNED_SERVERS_DESCRIPTION,
            setting_name=self.SETTING_NAME,
            callback=self._on_focus_outside_entry
        )
        self._controller = controller
        self._tray_indicator = tray_indicator

    def _on_focus_outside_entry(self, entry: Gtk.Entry, _: Gdk.EventFocus, __: EntryWidget):
        self.save_setting(entry.get_text())
        self._tray_indicator.reload_pinned_servers()

    def get_setting(self):
        """Shortcut property that sets the new setting and stores to disk."""
        tray_pinned_servers = get_setting(self._controller, self.SETTING_NAME)
        return ', '.join(tray_pinned_servers)

    def save_setting(self, new_value: List[str]):  # noqa: F811
        """Returns if the the upgrade tag has overridden original interactive
        object."""
        server_list = []

        for pinned_server in new_value.split(","):
            cleaned_pinned_server = pinned_server.strip().upper()

            if cleaned_pinned_server:
                server_list.append(cleaned_pinned_server)

        save_setting(self._controller, self.SETTING_NAME, server_list)


class GeneralSettings(BaseCategoryContainer):  # pylint: disable=too-many-instance-attributes
    """General settings are grouped under this class."""
    CATEGORY_NAME = "General"
    CONNECT_AT_APP_STARTUP_LABEL = "Auto connect"
    CONNECT_AT_APP_STARTUP_DESCRIPTION = "You will be connected to a server as "\
        "soon as Proton VPN app starts. Replace it with a country ISO code "\
        "(e.g.: US for United States), a server (e.g.: NL#42)"\
        " or Fastest for quick connection. Default value: Off."
    START_APP_MINIMIZED_LABEL = "Start app minimized"
    START_APP_MINIMIZED_DESCRIPTION = "When enabled, the app starts minimized "\
        "to the tray."
    ANONYMOUS_CRASH_REPORTS_LABEL = "Share anonymous crash reports"
    ANONYMOUS_CRASH_REPORTS_DESCRIPTION = "Crash reports help us fix bugs, detect firewalls, "\
        "and avoid VPN blocks.\n\nThese statistics do not contain your IP address, and they "\
        "cannot be used to identify you. We'll never share them with third parties."

    def __init__(
        self, controller: Controller,
        tray_indicator: Optional["TrayIndicator"] = None,
    ):
        super().__init__(self.CATEGORY_NAME)
        self._controller = controller
        self._tray_indicator = tray_indicator

    def build_ui(self):
        """Builds the UI, invoking all necessary methods that are
        under this category."""
        self.build_connect_at_app_startup()

        if self._tray_indicator:
            self.build_start_app_minimized()
            self.build_tray_pinned_servers()

        self.build_anonymous_crash_reports()

        if self._controller.feature_flags.get("LinuxBetaToggle"):
            self.build_beta_upgrade()

    def build_connect_at_app_startup(self):
        """Builds and adds the `connect_at_app_startup` setting to the widget."""
        def on_focus_out_callback(entry: Gtk.Entry, _: Gdk.EventFocus, entry_widget: EntryWidget):
            new_value = entry.get_text().strip().upper()
            if new_value == "OFF":
                new_value = None

            entry_widget.save_setting(new_value)

        self.pack_start(EntryWidget(
            controller=self._controller,
            title=self.CONNECT_AT_APP_STARTUP_LABEL,
            description=self.CONNECT_AT_APP_STARTUP_DESCRIPTION,
            setting_name="app_configuration.connect_at_app_startup",
            callback=on_focus_out_callback
        ), False, False, 0)

    def build_start_app_minimized(self):
        """Builds and adds the `start_app_minimized` setting to the widget."""
        self.pack_start(ToggleWidget(
            controller=self._controller,
            title=self.START_APP_MINIMIZED_LABEL,
            description=self.START_APP_MINIMIZED_DESCRIPTION,
            setting_name="app_configuration.start_app_minimized"
        ), False, False, 0)

    def build_tray_pinned_servers(self):
        """Builds and adds the `tray_pinned_servers` setting to the widget."""
        self.pack_start(TrayPinnedServersWidget(
            controller=self._controller, tray_indicator=self._tray_indicator
        ), False, False, 0)

    def build_anonymous_crash_reports(self):
        """Builds and adds the `anonymous_crash_reports` setting to the widget."""
        self.pack_start(ToggleWidget(
            controller=self._controller,
            title=self.ANONYMOUS_CRASH_REPORTS_LABEL,
            description=self.ANONYMOUS_CRASH_REPORTS_DESCRIPTION,
            setting_name="settings.anonymous_crash_reports"
        ), False, False, 0)

    def build_beta_upgrade(self):
        """Builds and adds the `Early Access` setting to the widget."""
        early_access = EarlyAccessWidget(self._controller)

        if not early_access.can_early_access_be_displayed():
            return

        self.pack_start(early_access, False, False, 0)
