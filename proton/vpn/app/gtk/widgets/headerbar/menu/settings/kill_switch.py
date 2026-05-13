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
from types import ModuleType
from typing import Callable, Optional

from gi.repository import Gtk

from proton.vpn.app.gtk.controller import Controller
from proton.vpn.app.gtk.utils.safe_signal_connect import safe_signal_connect
from proton.vpn.connection.enum import KillSwitchSetting\
    as KillSwitchSettingEnum

from proton.vpn.app.gtk.widgets.headerbar.menu.settings.common\
    import ConflictableToggleWidget, SettingDescription, SettingName
from proton.vpn.app.gtk.widgets.headerbar.menu.settings.common import (
    ReactiveSetting
)

class KillSwitchWidget(ConflictableToggleWidget, ReactiveSetting):  # noqa pylint: disable=too-many-instance-attributes,too-few-public-methods
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

    def __init__(self, controller: Controller, gtk: Optional[ModuleType] = None,
                 conflict_resolver: Optional[Callable] = None):
        super().__init__(
            controller=controller,
            title=self.KILLSWITCH_LABEL,
            description=self.KILLSWITCH_DESCRIPTION,
            setting_name=self.SETTING_NAME,
            do_set=self._do_set,
            do_revert=self._do_revert,
            disable_on_active_connection=True,
            conflict_resolver=conflict_resolver,
        )

        self.gtk = gtk or Gtk
        self._controller = controller
        self._standard_radio_button_connect_id = None
        self._advanced_radio_button_connect_id = None

        self.standard_radio_button: Optional[Gtk.CheckButton] = None
        self.advanced_radio_button: Optional[Gtk.CheckButton] = None
        self.revealer: Optional[Gtk.Revealer] = None

    def build_revealer(self):
        """Builds the revealer"""
        self.revealer = self.gtk.Revealer()
        self.attach(self.revealer, 0, 2, 2, 1)
        revealer_container = self._build_revealer_container()
        self.revealer.set_child(revealer_container)
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
        revealer_container.append(self._build_standard_killswitch())
        revealer_container.append(self._build_advanced_killswitch())

        return revealer_container

    def _build_standard_killswitch(self) -> Gtk.Grid:
        main_standard_container = self.gtk.Grid()
        main_standard_container.set_column_spacing(10)

        self.standard_radio_button = Gtk.CheckButton()
        self.standard_radio_button.set_active(self.get_setting() == KillSwitchSettingEnum.ON)

        main_standard_container.attach(self.standard_radio_button, 0, 0, 1, 1)
        main_standard_container.attach(SettingName("Standard"), 1, 0, 1, 1)
        main_standard_container.attach(
            SettingDescription(self.KILLSWITCH_STANDARD_DESCRIPTION),
            1, 1, 1, 1
        )

        safe_signal_connect(
            self.standard_radio_button,
            "toggled",
            self._on_standard_radio_button_toggle
        )

        return main_standard_container

    def _build_advanced_killswitch(self) -> Gtk.Grid:
        main_advanced_container = self.gtk.Grid()
        main_advanced_container.set_column_spacing(10)

        self.advanced_radio_button = Gtk.CheckButton()
        self.advanced_radio_button.set_group(self.standard_radio_button)
        self.advanced_radio_button.set_active(self.get_setting() == KillSwitchSettingEnum.PERMANENT)

        main_advanced_container.attach(self.advanced_radio_button, 0, 0, 1, 1)
        main_advanced_container.attach(SettingName("Advanced"), 1, 0, 1, 1)
        main_advanced_container.attach(
            SettingDescription(self.KILLSWITCH_ADVANCED_DESCRIPTION),
            1, 1, 1, 1
        )

        safe_signal_connect(
            self.advanced_radio_button,
            "toggled",
            self._on_advanced_radio_button_toggle
        )

        return main_advanced_container

    def _on_standard_radio_button_toggle(self, button):
        self._handle_toggle(button, KillSwitchSettingEnum.ON)

    def _on_advanced_radio_button_toggle(self, button):
        self._handle_toggle(button, KillSwitchSettingEnum.PERMANENT)

    def _handle_toggle(self, radio_button: Gtk.CheckButton, new_value: int):
        # If revealer is hidden then we don't want to resolve the trigger from
        # programmatically setting the standard radio button.
        if not self.revealer.get_reveal_child():
            return

        if radio_button.get_active():
            self.save_setting(new_value)

    def _do_set(self, _toggle, new_value: bool):
        self.save_setting(int(new_value))
        self.revealer.set_reveal_child(new_value)

        self.standard_radio_button.set_active(True)

    def _do_revert(self, _toggle):
        self.switch.set_active(False)

    def get_killswitch_state(self) -> KillSwitchSettingEnum:
        """Returns the current kill switch state."""
        if self.switch.get_active():
            if self.standard_radio_button.get_active():
                return KillSwitchSettingEnum.ON
            if self.advanced_radio_button.get_active():
                return KillSwitchSettingEnum.PERMANENT
        return KillSwitchSettingEnum.OFF

    def set_killswitch_state(self, state: KillSwitchSettingEnum):
        """Returns the current kill switch state."""

        if state == KillSwitchSettingEnum.ON:
            self.switch.set_active(True)
            self.standard_radio_button.set_active(True)
        elif state == KillSwitchSettingEnum.PERMANENT:
            self.switch.set_active(True)
            self.advanced_radio_button.set_active(True)
        else:
            self.switch.set_active(False)

    def on_settings_changed(self, settings):
        if self.get_killswitch_state() != settings.killswitch:
            self.set_killswitch_state(settings.killswitch)
