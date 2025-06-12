"""
Copyright (c) 2025 Proton AG

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
from typing import Union

from gi.repository import Gtk, Gdk

from proton.vpn.app.gtk.controller import Controller

from proton.vpn.app.gtk.widgets.headerbar.menu.settings.common import ToggleWidget, EntryWidget


class AppPathWidget(EntryWidget):
    """Contains the split tunneling widget.
    """
    def __init__(self, controller: Controller):
        super().__init__(
            controller=controller,
            title="App paths",
            setting_name="settings.features.split_tunneling.config.app_paths",
            description="",
            requires_subscription_to_be_active=True
        )

    # pylint: disable=R0801
    def _on_focus_out_callback(self, entry_widget: Gtk.Entry, _: Gdk.EventFocus):
        app_paths = []
        for app_path in entry_widget.get_text().split(","):
            app_paths.append(app_path.strip())

        self.save_setting(app_paths)

    def _build_entry(self) -> Gtk.Entry:
        entry = Gtk.Entry()
        value = self._get_setting()
        if value is None:
            value = ""

        entry.set_text(str(value))
        entry.connect("focus-out-event", self._on_focus_out_callback)

        return entry

    def _get_setting(self) -> Union[str, list[str]]:
        """Shortcut property that returns the current setting"""
        app_paths = super().get_setting()
        return ', '.join(app_paths)


class SplitTunnelingWidget(ToggleWidget):
    """Contains the split tunneling widget.
    """
    def __init__(
            self,
            controller: Controller,
            app_path_widget: AppPathWidget = None,
            gtk: Gtk = None
    ):
        super().__init__(
            controller=controller,
            title="Split Tunneling",
            setting_name="settings.features.split_tunneling.enabled",
            description="Prevent traffic from going through VPN",
            callback=self._on_switch_button_toggle
        )
        self.gtk = gtk or Gtk
        self.revealer = None
        self.app_path_widget = app_path_widget or AppPathWidget(controller=controller)

    # pylint: disable=R0801
    @staticmethod
    def build(controller: Controller) -> SplitTunnelingWidget:
        """Shortcut method to initialize widget."""
        widget = SplitTunnelingWidget(controller)
        widget.build_revealer()
        return widget

    def build_revealer(self):
        """Builds the revealer"""
        self.revealer = self.gtk.Revealer()
        self.attach(self.revealer, 0, 2, 2, 1)
        revealer_container = self._build_revealer_container()
        self.revealer.add(revealer_container)
        print("is ST enabled: ", self.get_setting())
        self.revealer.set_reveal_child(self.get_setting())

    def _build_revealer_container(self) -> Gtk.Box:
        # Add both containers that contain all children that are to be displayed in the revealer
        revealer_container = self.gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        revealer_container.set_spacing(10)
        revealer_container.pack_start(self.app_path_widget, False, False, 0)

        return revealer_container

    def _on_switch_button_toggle(self, _, new_value: bool, __):
        self.save_setting(new_value)
        self.revealer.set_reveal_child(new_value)
