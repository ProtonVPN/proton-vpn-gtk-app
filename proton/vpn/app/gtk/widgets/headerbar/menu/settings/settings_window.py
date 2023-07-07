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

from gi.repository import Gtk
from proton.vpn.app.gtk.controller import Controller
from proton.vpn.app.gtk.widgets.main.notification_bar import NotificationBar
from proton.vpn.app.gtk.widgets.headerbar.menu.settings.connection_settings import \
    ConnectionSettings
from proton.vpn.app.gtk.widgets.headerbar.menu.settings.feature_settings import \
    FeatureSettings


class SettingsWindow(Gtk.Window):
    """Main settings window."""
    def __init__(
        self,
        controller: Controller,
        notification_bar: NotificationBar = None,
        feature_settings: FeatureSettings = None,
        connection_settings: ConnectionSettings = None
    ):
        super().__init__()
        self.set_title("Settings")
        self.set_default_size(600, 500)
        self.set_modal(True)

        self._controller = controller
        self._notification_bar = notification_bar or NotificationBar()

        self._feature_settings = feature_settings or FeatureSettings(
            self._controller, self._notification_bar
        )
        self._connection_settings = connection_settings or ConnectionSettings(
            self._controller, self._notification_bar
        )

        self._create_elastic_window()

        self.connect("realize", self._build_ui)

    def _build_ui(self, *_):
        self._connection_settings.build_ui()
        self._feature_settings.build_ui()
        self.show_all()

    def _create_elastic_window(self):
        """This allows for the content to be always centered and expand or contract
        based on window size.

        The reason we use two containers is mainly due to the notification bar, as this
        way the notification will span across the entire window while only the
        settings will be centered.
        """
        self.main_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.content_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

        self.content_container.pack_start(self._feature_settings, False, False, 0)
        self.content_container.pack_start(self._connection_settings, False, False, 0)

        viewport = Gtk.Viewport()
        viewport.get_style_context().add_class("viewport-frame")
        viewport.add(self.content_container)

        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_property("window-placement", False)
        scrolled_window.set_propagate_natural_height(True)
        scrolled_window.set_min_content_height(300)
        scrolled_window.set_min_content_width(400)
        scrolled_window.add(viewport)

        self.main_container.pack_start(self._notification_bar, False, False, 0)
        self.main_container.pack_start(scrolled_window, False, False, 0)

        self.add(self.main_container)
