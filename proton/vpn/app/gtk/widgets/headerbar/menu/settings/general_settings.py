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
from typing import TYPE_CHECKING, Optional
from gi.repository import Gtk
from proton.vpn.app.gtk.controller import Controller
from proton.vpn.app.gtk.widgets.headerbar.menu.settings.common import (
    BaseCategoryContainer, SettingRow, SettingName, SettingDescription
)
if TYPE_CHECKING:
    from proton.vpn.app.gtk.widgets.main.tray_indicator import TrayIndicator


class GeneralSettings(BaseCategoryContainer):  # pylint: disable=too-many-instance-attributes
    """General settings are grouped under this class."""
    CATEGORY_NAME = "General"
    CONNECT_AT_APP_STARTUP_LABEL = "Auto connect"
    CONNECT_AT_APP_STARTUP_DESCRIPTION = "You will be connected to a server as "\
        "soon as Proton VPN app starts. Replace it with a country ISO code "\
        "(e.g.: US for United States), a server (e.g.: NL#42)"\
        " or Fastest for quick connection. Default value: Off."
    TRAY_PINNED_SERVERS_LABEL = "Pinned tray connections"
    TRAY_PINNED_SERVERS_DESCRIPTION = "Access preferred connections from system tray."\
        " Enter country or server codes, separated by commas, to quickly connect "\
        "(e.g.: NL#42, JP, US, IT#01)."
    ANONYMOUS_CRASH_REPORTS_LABEL = "Share anonymous crash reports"
    ANONYMOUS_CRASH_REPORTS_DESCRIPTION = "Crash reports help us fix bugs, detect firewalls, "\
        "and avoid VPN blocks.\n\nThese statistics do not contain your IP address, and they "\
        "cannot be used to identify you. We'll never share them with third parties."

    def __init__(
        self, controller: Controller,
        tray_indicator: Optional["TrayIndicator"] = None
    ):
        super().__init__(self.CATEGORY_NAME)
        self._controller = controller
        self._tray_indicator = tray_indicator

        self.connect_at_app_startup_row = None
        self.tray_pinned_servers_row = None
        self.anonymous_crash_reports_row = None

    def build_ui(self):
        """Builds the UI, invoking all necessary methods that are
        under this category."""
        self.build_connect_at_app_startup()
        self.build_tray_pinned_servers()
        self.build_anonymous_crash_reports()

    @property
    def connect_at_app_startup(self) -> str:
        """Shortcut property that returns the current
        `connect_at_app_startup` setting"""
        connect_at_app_startup = self._controller.app_configuration.connect_at_app_startup

        if connect_at_app_startup is None:
            return "Off"

        return connect_at_app_startup

    @connect_at_app_startup.setter
    def connect_at_app_startup(self, newvalue: str):
        """Shortcut property that sets the new `connect_at_app_startup` setting and
        stores to disk."""
        app_config = self._controller.app_configuration
        app_config.connect_at_app_startup = newvalue
        self._controller.app_configuration = app_config

    def build_connect_at_app_startup(self):
        """Builds and adds the `connect_at_app_startup` setting to the widget."""
        def on_focus_outside_entry(entry: Gtk.Entry, _):
            newvalue = entry.get_text().strip().upper()

            if newvalue == "OFF":
                newvalue = None

            self.connect_at_app_startup = newvalue

        entry = Gtk.Entry()
        entry.set_text(self.connect_at_app_startup)
        entry.connect("focus-out-event", on_focus_outside_entry)

        self.connect_at_app_startup_row = SettingRow(
            SettingName(self.CONNECT_AT_APP_STARTUP_LABEL),
            entry,
            SettingDescription(self.CONNECT_AT_APP_STARTUP_DESCRIPTION),
        )

        self.pack_start(self.connect_at_app_startup_row, False, False, 0)

    @property
    def tray_pinned_servers(self) -> str:
        """Shortcut property that returns the current
        `tray_pinned_servers` setting"""
        tray_pinned_servers = self._controller.app_configuration.tray_pinned_servers

        return ', '.join(tray_pinned_servers)

    @tray_pinned_servers.setter
    def tray_pinned_servers(self, newvalue: str):
        """Shortcut property that sets the new `tray_pinned_servers` setting and
        stores to disk."""
        server_list = []

        for pinned_server in newvalue.split(","):
            cleaned_pinned_server = pinned_server.strip().upper()

            if cleaned_pinned_server:
                server_list.append(cleaned_pinned_server)

        app_config = self._controller.app_configuration
        app_config.tray_pinned_servers = server_list
        self._controller.app_configuration = app_config

    def build_tray_pinned_servers(self):
        """Builds and adds the `tray_pinned_servers` setting to the widget."""
        def on_focus_outside_entry(entry: Gtk.Entry, _):
            self.tray_pinned_servers = entry.get_text()
            self._tray_indicator.reload_pinned_servers()

        if self._tray_indicator is None:
            return

        entry = Gtk.Entry()
        entry.set_text(self.tray_pinned_servers)
        entry.connect("focus-out-event", on_focus_outside_entry)

        self.tray_pinned_servers_row = SettingRow(
            SettingName(self.TRAY_PINNED_SERVERS_LABEL),
            entry,
            SettingDescription(self.TRAY_PINNED_SERVERS_DESCRIPTION),
        )

        self.pack_start(self.tray_pinned_servers_row, False, False, 0)

    @property
    def anonymous_crash_reports(self) -> bool:
        """Shortcut property that returns the current `anonymous_crash_reports` setting"""
        return self._controller.get_settings().anonymous_crash_reports

    @anonymous_crash_reports.setter
    def anonymous_crash_reports(self, newvalue: bool):
        """Shortcut property that sets the new `anonymous_crash_reports` setting and
        stores to disk."""
        self._controller.get_settings().anonymous_crash_reports = newvalue
        self._controller.save_settings()

    def build_anonymous_crash_reports(self):
        """Builds and adds the `anonymous_crash_reports` setting to the widget."""
        def on_switch_state(_, new_value: bool):
            self.anonymous_crash_reports = new_value

        switch = Gtk.Switch()

        self.anonymous_crash_reports_row = SettingRow(
            SettingName(self.ANONYMOUS_CRASH_REPORTS_LABEL),
            switch,
            SettingDescription(self.ANONYMOUS_CRASH_REPORTS_DESCRIPTION)
        )

        switch.set_state(self.anonymous_crash_reports)
        switch.connect("state-set", on_switch_state)
        self.pack_start(self.anonymous_crash_reports_row, False, False, 0)
