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


class SettingsWindow(Gtk.Window):
    """Main settings window."""
    def __init__(
        self,
        controller: Controller,
        notification_bar: NotificationBar = None,
        connection_settings: ConnectionSettings = None
    ):
        super().__init__()
        self.set_title("Settings")
        self.set_default_size(600, 500)
        self.set_modal(True)

        self._container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self._container.set_name("settings-widget")

        self._controller = controller
        self._notification_bar = notification_bar or NotificationBar()

        self._connection_settings = connection_settings or ConnectionSettings(
            self._controller, self._notification_bar
        )

        self._container.pack_start(self._notification_bar, False, False, 0)
        self._container.pack_start(self._connection_settings, False, False, 0)

        self.add(self._container)

        self.connect("realize", self._build_ui)

    def _build_ui(self, *_):
        self._connection_settings.build_ui()
        self.show_all()


class ConnectionSettings(Gtk.Box):
    """Settings related to connection are all grouped under this class."""

    PROTOCOL_LABEL = "Protocol"
    VPN_ACCELERATOR_LABEL = "VPN Accelerator"
    VPN_ACCELERATOR_DESCRIPTION = "Increase your connection speed by up to 400% "\
        "with performance enhancing technologies."
    RECONNECT_MESSAGE = "Please establish a new VPN connection for "\
        "changes to take effect."

    def __init__(self, controller: Controller, notification_bar: NotificationBar):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self._controller = controller
        self._notification_bar = notification_bar

        self.set_halign(Gtk.Align.CENTER)
        self.set_spacing(15)

        self.vpn_accelerator_switch = None
        self.protocol_combobox = None

    def build_ui(self):
        """Builds the UI, invoking all necessary methods that are
        under this category."""
        self.get_style_context().add_class("setting-category")
        self._build_widget_title()
        self._build_protocol()
        self._build_vpn_accelerator()

    @property
    def vpn_accelerator(self) -> bool:
        """Shortcut property that returns the current `vpn_accelerator` setting"""
        return self._controller.get_settings().features.vpn_accelerator

    @vpn_accelerator.setter
    def vpn_accelerator(self, newvalue: bool):
        """Shortcut property that sets the new `vpn_accelerator` setting and
        stores to disk."""
        self._controller.get_settings().features.vpn_accelerator = newvalue
        self._controller.save_settings()

    @property
    def protocol(self) -> bool:
        """Shortcut property that returns the current `protocol` setting"""
        return self._controller.get_settings().protocol

    @protocol.setter
    def protocol(self, newvalue: bool):
        """Shortcut property that sets the new `protocol` setting and
        stores to disk."""
        self._controller.get_settings().protocol = newvalue
        self._controller.save_settings()

    def _build_widget_title(self):
        """Builds and adds the title label of this category to the widget."""
        title_label = Gtk.Label(label="Connection")
        title_label.set_halign(Gtk.Align.START)
        style_context = title_label.get_style_context()
        style_context.add_class("heading")
        self.pack_start(title_label, False, False, 0)

    def _build_vpn_accelerator(self):
        """Builds and adds the `vpn_accelerator` setting to the widget."""
        def on_switch_state(_, new_value: bool):
            self.vpn_accelerator = new_value
            if self._controller.is_connection_active:
                self._notification_bar.show_info_message(
                    f"{self.RECONNECT_MESSAGE}"
                )

        setting_grid = Gtk.Grid()
        setting_grid.get_style_context().add_class("setting-item")
        setting_grid.set_halign(Gtk.Align.FILL)
        setting_grid.set_row_spacing(10)
        setting_grid.set_column_spacing(200)

        label = Gtk.Label(label=self.VPN_ACCELERATOR_LABEL)
        label.set_halign(Gtk.Align.START)

        self.vpn_accelerator_switch = Gtk.Switch()
        self.vpn_accelerator_switch.set_halign(Gtk.Align.END)
        self.vpn_accelerator_switch.set_state(self.vpn_accelerator)
        self.vpn_accelerator_switch.connect("state-set", on_switch_state)

        description = Gtk.Label(label=self.VPN_ACCELERATOR_DESCRIPTION)
        description.set_line_wrap(True)
        description.set_max_width_chars(1)
        description.set_property("xalign", 0)

        setting_grid.attach(label, 0, 0, 1, 1)
        setting_grid.attach(self.vpn_accelerator_switch, 1, 0, 1, 1)
        setting_grid.attach(description, 0, 1, 2, 1)

        self.pack_start(setting_grid, False, False, 0)

    def _build_protocol(self):
        """Builds and adds the `protocol` setting to the widget."""
        def on_combobox_changed(combobox):
            model = combobox.get_model()
            treeiter = combobox.get_active_iter()
            protocol = model[treeiter][0]
            self.protocol = protocol
            if self._controller.is_connection_active:
                self._notification_bar.show_info_message(
                    f"{self.RECONNECT_MESSAGE}"
                )

        setting_grid = Gtk.Grid()
        setting_grid.get_style_context().add_class("setting-item")
        setting_grid.set_halign(Gtk.Align.FILL)
        setting_grid.set_row_spacing(10)
        setting_grid.set_column_spacing(200)

        label = Gtk.Label(label=self.PROTOCOL_LABEL)
        label.set_halign(Gtk.Align.START)

        available_protocols = self._controller.get_available_protocols()
        self.protocol_combobox = Gtk.ComboBoxText()

        for protocol in available_protocols:
            self.protocol_combobox.append(protocol, protocol)

        self.protocol_combobox.set_entry_text_column(1)
        self.protocol_combobox.set_active_id(self.protocol)
        self.protocol_combobox.connect("changed", on_combobox_changed)

        setting_grid.attach(label, 0, 0, 1, 1)
        setting_grid.attach(self.protocol_combobox, 1, 0, 1, 1)

        self.pack_start(setting_grid, False, False, 0)
