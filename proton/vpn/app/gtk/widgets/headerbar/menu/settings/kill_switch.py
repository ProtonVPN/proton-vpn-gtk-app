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
from typing import Union

from gi.repository import Gtk, Gdk

from proton.vpn.app.gtk.controller import Controller
from proton.vpn.connection.enum import KillSwitchSetting as KillSwitchSettingEnum

from proton.vpn.app.gtk.widgets.headerbar.menu.settings.common import ToggleWidget, EntryWidget, \
    SettingDescription, SettingName

class KillSwitchWidget(ToggleWidget):  # noqa pylint: disable=too-many-instance-attributes,too-few-public-methods
    """Kill switch setting widget.

    Since the kill switch can have multiple modes, we need to have a proper
    widget that handles of all of these cases and is easy to test.
    """
    KILLSWITCH_LABEL = "Kill switch"
    KILLSWITCH_DESCRIPTION = "Protects your IP address by disconnecting you from the " \
        "internet if you lose your VPN connection. "\
        "<a href=\"https://protonvpn.com/support/what-is-kill-switch/\">Learn more</a> \n\n" \
        "Kill switch can only be changed when VPN is disconnected."
    KILLSWITCH_STANDARD_DESCRIPTION = "Automatically disconnect from the internet if "\
        "VPN connection is lost."
    KILLSWITCH_ADVANCED_DESCRIPTION = "Only allow internet access when connected to Proton VPN. " \
        "Advanced kill switch will remain active even when you restart your device."
    SETTING_NAME = "settings.killswitch"

    def __init__(self, controller: Controller, gtk: Gtk = None):
        super().__init__(
            controller=controller,
            title=self.KILLSWITCH_LABEL,
            description=self.KILLSWITCH_DESCRIPTION,
            setting_name=self.SETTING_NAME,
            callback=self._on_switch_button_toggle,
            disable_on_active_connection=True
        )

        self.gtk = gtk or Gtk
        self._controller = controller
        self._standard_radio_button_connect_id = None
        self._advanced_radio_button_connect_id = None

        self.standard_radio_button = None
        self.advanced_radio_button = None
        self.revealer = None

    def build_revealer(self):
        """Builds the revealer"""
        self.revealer = self.gtk.Revealer()
        self.attach(self.revealer, 0, 2, 2, 1)
        revealer_container = self._build_revealer_container()
        self.revealer.add(revealer_container)
        self.revealer.set_reveal_child(self.get_setting() > KillSwitchSettingEnum.OFF)

    @staticmethod
    def build(controller: Controller) -> "KillSwitchWidget":
        """Shortcut method to initialize widget."""
        widget = KillSwitchWidget(controller)
        widget.build_revealer()
        return widget

    def _build_revealer_container(self) -> Gtk.Box:
        # Add both containers that contain all children that are to be displayed in the revealer
        revealer_container = self.gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        revealer_container.set_spacing(10)
        revealer_container.pack_start(self._build_standard_killswitch(), False, False, 0)
        revealer_container.pack_start(self._build_advanced_killswitch(), False, False, 0)

        return revealer_container

    def _build_standard_killswitch(self) -> Gtk.Grid:
        main_standard_container = self.gtk.Grid()
        main_standard_container.set_column_spacing(10)

        self.standard_radio_button = self.gtk.RadioButton()
        self.standard_radio_button.set_active(self.get_setting() == KillSwitchSettingEnum.ON)

        main_standard_container.attach(self.standard_radio_button, 0, 0, 1, 1)
        main_standard_container.attach(SettingName("Standard"), 1, 0, 1, 1)
        main_standard_container.attach(
            SettingDescription(self.KILLSWITCH_STANDARD_DESCRIPTION),
            1, 1, 1, 1
        )

        self.standard_radio_button.connect(
            "toggled", self._on_radio_button_toggle, KillSwitchSettingEnum.ON
        )

        return main_standard_container

    def _build_advanced_killswitch(self) -> Gtk.Grid:
        main_advanced_container = self.gtk.Grid()
        main_advanced_container.set_column_spacing(10)

        self.advanced_radio_button = self.gtk.RadioButton(group=self.standard_radio_button)
        self.advanced_radio_button.set_active(self.get_setting() == KillSwitchSettingEnum.PERMANENT)

        main_advanced_container.attach(self.advanced_radio_button, 0, 0, 1, 1)
        main_advanced_container.attach(SettingName("Advanced"), 1, 0, 1, 1)
        main_advanced_container.attach(
            SettingDescription(self.KILLSWITCH_ADVANCED_DESCRIPTION),
            1, 1, 1, 1
        )

        self.advanced_radio_button.connect(
            "toggled", self._on_radio_button_toggle, KillSwitchSettingEnum.PERMANENT
        )

        return main_advanced_container

    def _on_radio_button_toggle(self, radio_button: Gtk.RadioButton, new_value: int):
        # If revealer is hidden then we don't want to resolve the trigger from
        # programmatically setting the standard radio button.
        if not self.revealer.get_reveal_child():
            return

        if radio_button.get_active():
            self._update(new_value, False)

    def _on_switch_button_toggle(self, _, new_value: bool, __):
        self._update(int(new_value), True)

    def _update(self, value: int, new_value_comes_from_main_switch: bool):
        self.save_setting(value)
        self.revealer.set_reveal_child(value > KillSwitchSettingEnum.OFF)

        if new_value_comes_from_main_switch:
            self.standard_radio_button.set_active(True)


class SplitTunnelingWidget(EntryWidget):
    """Contains the split tunneling widget.
    """
    def __init__(self, controller):
        super().__init__(
            controller,
            "Split Tunneling",
            "settings.features.split_tunneling.app_paths",
            "Prevent traffic from going through VPN"
        )

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
