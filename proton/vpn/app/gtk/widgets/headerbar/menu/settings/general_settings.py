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

from gi.repository import Gtk
from proton.vpn.app.gtk.controller import Controller
from proton.vpn.app.gtk.widgets.main.notification_bar import NotificationBar
from proton.vpn.app.gtk.widgets.headerbar.menu.settings.common import (
    CategoryHeader, SettingRow, SettingName, SettingDescription
)


class GeneralSettings(Gtk.Box):  # pylint: disable=too-many-instance-attributes
    """General settingsa are grouped under this class."""
    CATEGORY_NAME = "General"
    CONNECT_AT_APP_STARTUP_LABEL = "Auto Connect"
    CONNECT_AT_APP_STARTUP_DESCRIPTION = "You will be connected to a server as "\
        "soon as Proton VPN app starts. Replace it with a country ISO code "\
        "(e.g.: US for United States), a server (e.g.: NL#42)"\
        " or Fastest for quick connection. Default value: Off."

    def __init__(self, controller: Controller, notification_bar: NotificationBar):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self._controller = controller
        self._notification_bar = notification_bar

        self.connect_at_app_startup_row = None

        self.set_halign(Gtk.Align.FILL)
        self.set_spacing(15)

        self.get_style_context().add_class("setting-category")

    def build_ui(self):
        """Builds the UI, invoking all necessary methods that are
        under this category."""
        self.pack_start(CategoryHeader(self.CATEGORY_NAME), False, False, 0)
        self.build_connect_at_app_startup()

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
        entry.set_halign(Gtk.Align.END)
        entry.set_hexpand(True)

        entry.set_text(self.connect_at_app_startup)
        entry.connect("focus-out-event", on_focus_outside_entry)

        self.connect_at_app_startup_row = SettingRow(
            SettingName(self.CONNECT_AT_APP_STARTUP_LABEL),
            entry,
            SettingDescription(self.CONNECT_AT_APP_STARTUP_DESCRIPTION),
        )

        self.pack_start(self.connect_at_app_startup_row, False, False, 0)
