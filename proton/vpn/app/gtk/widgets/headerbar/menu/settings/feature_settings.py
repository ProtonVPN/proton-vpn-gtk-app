"""
Feature settings module.


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
from proton.vpn.core.settings import NetShield
from proton.vpn.app.gtk.controller import Controller
from proton.vpn.app.gtk.widgets.main.notification_bar import NotificationBar
from proton.vpn.app.gtk.widgets.headerbar.menu.settings.common import (
    RECONNECT_MESSAGE, BaseCategoryContainer, SettingRow, SettingName, SettingDescription
)
from proton.vpn.connection.enum import KillSwitchSetting as KillSwitchSettingEnum


class KillSwitchSetting(SettingRow):  # noqa pylint: disable=too-many-instance-attributes,too-few-public-methods
    """Kill switch setting widget.

    Since the kill switch can have multiple modes, we need to have a proper
    widget that handles of all of these cases and is easy to test.
    """
    KILLSWITCH_LABEL = "Kill switch"
    KILLSWITCH_DESCRIPTION = "Protects your IP address by disconnecting you from the " \
        "internet if you lose your VPN connection. "\
        "<a href=\"https://protonvpn.com/support/what-is-kill-switch/\">Learn more</a>"
    KILLSWITCH_STANDARD_DESCRIPTION = "Automatically disconnect from the internet if "\
        "VPN connection is lost."
    KILLSWITCH_ADVANCED_DESCRIPTION = "Only allow internet access when connected to Proton VPN. " \
        "Advanced kill switch will remain active even when you restart your device."

    def __init__(self, controller: Controller):
        self._controller = controller

        killswitch_state = self.killswitch
        switch = self._build_main_setting(killswitch_state)

        super().__init__(
            SettingName(self.KILLSWITCH_LABEL),
            switch,
            SettingDescription(self.KILLSWITCH_DESCRIPTION)
        )

        self._standard_radio_button_connect_id = None
        self._advanced_radio_button_connect_id = None

        self.standard_radio_button = None
        self.advanced_radio_button = None
        self.revealer = None

        self._build_revealer(killswitch_state)

    @property
    def killswitch(self) -> int:
        """Shortcut property that returns the current `killswitch` setting."""
        return int(self._controller.get_settings().killswitch)

    @killswitch.setter
    def killswitch(self, newvalue: int):
        """Shortcut property that sets the new `killswitch` setting and
        stores to disk."""
        self._controller.get_settings().killswitch = int(newvalue)
        self._controller.save_settings()

    def _build_main_setting(self, killswitch_state: int) -> Gtk.Switch:
        switch = Gtk.Switch()
        switch.set_state(killswitch_state)
        switch.connect("state-set", self._on_switch_button_toggle)

        return switch

    def _build_revealer(self, killswitch_state: int):
        # Standard kill switch setting
        main_standard_container = Gtk.Grid()
        main_standard_container.set_column_spacing(10)

        self.standard_radio_button = Gtk.RadioButton()
        self.standard_radio_button.set_active(killswitch_state == KillSwitchSettingEnum.ON)

        main_standard_container.attach(self.standard_radio_button, 0, 0, 1, 1)
        main_standard_container.attach(SettingName("Standard"), 1, 0, 1, 1)
        main_standard_container.attach(
            SettingDescription(self.KILLSWITCH_STANDARD_DESCRIPTION),
            1, 1, 1, 1
        )

        # Advanced kill switch setting
        main_advanced_container = Gtk.Grid()
        main_advanced_container.set_column_spacing(10)

        self.advanced_radio_button = Gtk.RadioButton(group=self.standard_radio_button)
        self.advanced_radio_button.set_active(killswitch_state == KillSwitchSettingEnum.PERMANENT)

        main_advanced_container.attach(self.advanced_radio_button, 0, 0, 1, 1)
        main_advanced_container.attach(SettingName("Advanced"), 1, 0, 1, 1)
        main_advanced_container.attach(
            SettingDescription(self.KILLSWITCH_ADVANCED_DESCRIPTION),
            1, 1, 1, 1
        )

        # Add both containers that contain all children that are to be displayed in the revealer
        revealer_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        revealer_container.set_spacing(10)
        revealer_container.pack_start(main_standard_container, False, False, 0)
        revealer_container.pack_start(main_advanced_container, False, False, 0)

        # Create and add revealer
        self.revealer = Gtk.Revealer()
        self.attach(self.revealer, 0, 2, 2, 1)
        self.revealer.add(revealer_container)
        self.revealer.set_reveal_child(killswitch_state > KillSwitchSettingEnum.OFF)

        self.standard_radio_button.connect(
            "toggled", self._on_radio_button_toggle, KillSwitchSettingEnum.ON
        )
        self.advanced_radio_button.connect(
            "toggled", self._on_radio_button_toggle, KillSwitchSettingEnum.PERMANENT
        )

    def _on_radio_button_toggle(self, widget: Gtk.RadioButton, new_value: int):
        # If revealer is hidden then we don't want to resolve the trigger from
        # programmatically setting the standard radio button.
        if not self.revealer.get_reveal_child():
            return

        if widget.get_active():
            self._update(new_value, False)

    def _on_switch_button_toggle(self, _, new_value: bool):
        self._update(int(new_value), True)

    def _update(self, value: int, new_value_comes_from_main_switch: bool):
        self.killswitch = value
        self.revealer.set_reveal_child(value > KillSwitchSettingEnum.OFF)

        if new_value_comes_from_main_switch:
            self.standard_radio_button.set_active(True)


class FeatureSettings(BaseCategoryContainer):  # pylint: disable=too-many-instance-attributes
    """Settings related to connection are all grouped under this class."""
    CATEGORY_NAME = "Features"
    NETSHIELD_LABEL = "NetShield"
    NETSHIELD_DESCRIPTION = "Protect yourself from ads, malware, and trackers "\
        "on websites and apps."
    PORT_FORWARDING_LABEL = "Port forwarding"
    PORT_FORWARDING_DESCRIPTION = "Bypass firewalls to connect to P2P servers "\
        "and devices on your local network."
    PORT_FORWARDING_SETUP_GUIDE = "Follow our "\
        "<a href=\"https://protonvpn.com/support/port-forwarding-manual-setup/"\
        "#how-to-use-port-forwarding\">guide</a>"\
        " to set it up."

    def __init__(self, controller: Controller, notification_bar: NotificationBar):
        super().__init__(self.CATEGORY_NAME)
        self._controller = controller
        self._notification_bar = notification_bar

        self.netshield_row = None
        self.killswitch_row = None
        self.port_forwarding_row = None

    def build_ui(self):
        """Builds the UI, invoking all necessary methods that are
        under this category."""
        self.build_netshield()
        self.build_killswitch()
        self.build_port_forwarding()

    @property
    def netshield(self) -> str:
        """Shortcut property that returns the current `netshield` setting"""
        return str(self._controller.get_settings().features.netshield)

    @netshield.setter
    def netshield(self, newvalue: str):
        """Shortcut property that sets the new `netshield` setting and
        stores to disk."""
        self._controller.get_settings().features.netshield = int(newvalue)
        self._controller.save_settings()

    @property
    def port_forwarding(self) -> str:
        """Shortcut property that returns the current `port_forwarding` setting"""
        return self._controller.get_settings().features.port_forwarding

    @port_forwarding.setter
    def port_forwarding(self, newvalue: str):
        """Shortcut property that sets the new `port_forwarding` setting and
        stores to disk."""
        self._controller.get_settings().features.port_forwarding = newvalue
        self._controller.save_settings()

    def build_netshield(self):
        """Builds and adds the `netshield` setting to the widget.
        It takes into considertaion the `clientconfig` value and if
        the user has the expected `tier` to be used. If the user has a
        lower tier then required then an upgrade UI is displayed.
        """
        def on_combobox_changed(combobox):
            model = combobox.get_model()
            treeiter = combobox.get_active_iter()
            netshield = model[treeiter][1]
            self.netshield = netshield
            if self._controller.is_connection_active:
                self._notification_bar.show_info_message(
                    f"{RECONNECT_MESSAGE}"
                )

        if not self._controller.vpn_data_refresher.client_config.feature_flags.netshield:
            if self.netshield:
                self.netshield = NetShield.NO_BLOCK.value
            return

        netshield_options = [
            (str(NetShield.NO_BLOCK.value), "Off"),
            (str(NetShield.BLOCK_MALICIOUS_URL.value), "Block Malware"),
            (str(NetShield.BLOCK_ADS_AND_TRACKING.value), "Block ads, trackers and malware"),
        ]
        combobox = Gtk.ComboBoxText()

        for netshield_option in netshield_options:
            id_, ui_friendly_text = netshield_option
            combobox.append(id_, ui_friendly_text)

        self.netshield_row = SettingRow(
            SettingName(self.NETSHIELD_LABEL),
            combobox,
            SettingDescription(self.NETSHIELD_DESCRIPTION),
            self._controller.user_tier
        )

        combobox.set_entry_text_column(1)
        combobox.set_active_id(self.netshield)
        combobox.connect("changed", on_combobox_changed)
        self.pack_start(self.netshield_row, False, False, 0)

    def build_killswitch(self):
        """Builds and adds the `killswitch` setting to the widget."""
        self.killswitch_row = KillSwitchSetting(self._controller)
        self.pack_start(self.killswitch_row, False, False, 0)

    def build_port_forwarding(self):
        """Builds and adds the `port_forwarding` setting to the widget."""
        def edit_description_based_on_setting(setting_value):
            description_value = self.PORT_FORWARDING_DESCRIPTION
            if setting_value:
                description_value = self.PORT_FORWARDING_SETUP_GUIDE

            description.set_label(description_value)

        def on_switch_state(_, new_value: bool):
            self.port_forwarding = new_value
            if self._controller.is_connection_active:
                self._notification_bar.show_info_message(
                    f"{RECONNECT_MESSAGE}"
                )
            edit_description_based_on_setting(new_value)

        if not self._controller.vpn_data_refresher.client_config.feature_flags.port_forwarding:
            if self.port_forwarding:
                self.port_forwarding = False
            return

        switch = Gtk.Switch()
        description = SettingDescription(self.PORT_FORWARDING_DESCRIPTION)

        self.port_forwarding_row = SettingRow(
            SettingName(self.PORT_FORWARDING_LABEL),
            switch,
            description,
            self._controller.user_tier
        )

        port_forwarding_setting = self.port_forwarding
        edit_description_based_on_setting(port_forwarding_setting)

        switch.set_state(port_forwarding_setting)
        switch.connect("state-set", on_switch_state)
        self.pack_start(self.port_forwarding_row, False, False, 0)
