"""
Connection settings module.


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
from typing import TYPE_CHECKING

from gi.repository import Gtk
from proton.vpn.app.gtk.controller import Controller
from proton.vpn.app.gtk.widgets.headerbar.menu.settings.common import (
    BaseCategoryContainer, SettingRow, SettingName, SettingDescription
)

if TYPE_CHECKING:
    from proton.vpn.app.gtk.widgets.headerbar.menu.settings.settings_window import \
        SettingsWindow


class ConnectionSettings(BaseCategoryContainer):  # pylint: disable=too-many-instance-attributes
    """Settings related to connection are all grouped under this class."""
    CATEGORY_NAME = "Connection"
    PROTOCOL_LABEL = "Protocol"
    VPN_ACCELERATOR_LABEL = "VPN Accelerator"
    VPN_ACCELERATOR_DESCRIPTION = "Increase your connection speed by up to 400% "\
        "with performance enhancing technologies."
    MODERATE_NAT_LABEL = "Moderate NAT"
    MODERATE_NAT_DESCRIPTION = "Disables randomization of the local addresses mapping. "\
        "This can slightly reduce connection security, but should allow direct "\
        "connections for online gaming and similar purposes."
    SWITCH_PROTOCOL_IF_CONNECTION_ACTIVE_DESCRIPTION = "Protocol selection "\
        "is disabled while VPN is active. Disconnect to make changes."
    IPV6_LABEL = "IPv6"
    IPV6_DESCRIPTION = "Tunnels IPv6 traffic through the VPN. "\
        "Can enhance compatibility with IPv6 networks."

    def __init__(self, controller: Controller, settings_window: "SettingsWindow"):
        super().__init__(self.CATEGORY_NAME)
        self._controller = controller

        self.vpn_accelerator_row = None
        self.protocol_row = None
        self.moderate_nat_row = None
        self.ipv6_row = None
        self._settings_window = settings_window

    def build_ui(self):
        """Builds the UI, invoking all necessary methods that are
        under this category."""
        self.build_protocol()
        self.build_vpn_accelerator()
        self.build_moderate_nat()
        if self._controller.feature_flags.get("IPv6Support"):
            self.build_ipv6()

    @property
    def protocol(self) -> str:
        """Shortcut property that returns the current `protocol` setting"""
        return self._controller.get_settings().protocol

    @protocol.setter
    def protocol(self, newvalue: str):
        """Shortcut property that sets the new `protocol` setting and
        stores to disk."""
        settings = self._controller.get_settings()
        settings.protocol = newvalue
        self._controller.save_settings(settings, update_certificate=True)

    @property
    def vpn_accelerator(self) -> bool:
        """Shortcut property that returns the current `vpn_accelerator` setting"""
        return self._controller.get_settings().features.vpn_accelerator

    @vpn_accelerator.setter
    def vpn_accelerator(self, newvalue: bool):
        """Shortcut property that sets the new `vpn_accelerator` setting and
        stores to disk."""
        settings = self._controller.get_settings()
        settings.features.vpn_accelerator = newvalue
        self._controller.save_settings(settings, update_certificate=True)

    @property
    def moderate_nat(self) -> bool:
        """Shortcut property that returns the current `moderate_nat` setting."""
        return self._controller.get_settings().features.moderate_nat

    @moderate_nat.setter
    def moderate_nat(self, newvalue: bool):
        """Shortcut property that sets the new `moderate_nat` setting and
        stores to disk."""
        settings = self._controller.get_settings()
        settings.features.moderate_nat = newvalue
        self._controller.save_settings(settings, update_certificate=True)

    @property
    def ipv6(self) -> str:
        """Shortcut property that returns the current `ipv6` setting"""
        return self._controller.get_settings().ipv6

    @ipv6.setter
    def ipv6(self, newvalue: str):
        """Shortcut property that sets the `ipv6` setting and
        stores to disk."""
        settings = self._controller.get_settings()
        settings.ipv6 = newvalue
        self._controller.save_settings(settings)

    def build_protocol(self):
        """Builds and adds the `protocol` setting to the widget."""
        def on_combobox_changed(combobox):
            model = combobox.get_model()
            treeiter = combobox.get_active_iter()
            protocol = model[treeiter][1]
            self.protocol = protocol

        available_protocols = self._controller.get_available_protocols()
        combobox = Gtk.ComboBoxText()

        for protocol in available_protocols:
            combobox.append(protocol.cls.protocol, protocol.cls.ui_protocol)

        combobox.set_entry_text_column(1)
        combobox.set_active_id(self.protocol)
        combobox.connect("changed", on_combobox_changed)

        self.protocol_row = SettingRow(SettingName(self.PROTOCOL_LABEL), combobox)

        if not self._controller.is_connection_disconnected:
            self.protocol_row.enabled = False
            self.protocol_row.set_tooltip(
                self.SWITCH_PROTOCOL_IF_CONNECTION_ACTIVE_DESCRIPTION
            )

        self.pack_start(self.protocol_row, False, False, 0)

    def build_vpn_accelerator(self):
        """Builds and adds the `vpn_accelerator` setting to the widget."""
        def on_switch_state(_, new_value: bool):
            self.vpn_accelerator = new_value
            self._settings_window.notify_user_with_reconnect_message()

        switch = Gtk.Switch()

        self.vpn_accelerator_row = SettingRow(
            SettingName(self.VPN_ACCELERATOR_LABEL),
            switch,
            SettingDescription(self.VPN_ACCELERATOR_DESCRIPTION),
            self._controller.user_tier
        )

        switch.set_state(self.vpn_accelerator)
        switch.connect("state-set", on_switch_state)
        self.pack_start(self.vpn_accelerator_row, False, False, 0)

    def build_moderate_nat(self):
        """Builds and adds the `moderate_nat` setting to the widget."""
        def on_switch_state(_, new_value: bool):
            self.moderate_nat = new_value
            self._settings_window.notify_user_with_reconnect_message()

        switch = Gtk.Switch()

        self.moderate_nat_row = SettingRow(
            SettingName(self.MODERATE_NAT_LABEL),
            switch,
            SettingDescription(self.MODERATE_NAT_DESCRIPTION),
            self._controller.user_tier
        )

        switch.set_state(self.moderate_nat)
        switch.connect("state-set", on_switch_state)
        self.pack_start(self.moderate_nat_row, False, False, 0)

    def build_ipv6(self):
        """Builds and adds the `ipv6` setting to the widget."""
        def on_switch_state(_, new_value: bool):
            self.ipv6 = new_value
            self._settings_window.notify_user_with_reconnect_message()

        switch = Gtk.Switch()

        self.ipv6_row = SettingRow(
            SettingName(self.IPV6_LABEL),
            switch,
            SettingDescription(self.IPV6_DESCRIPTION)
        )

        switch.set_state(self.ipv6)
        switch.connect("state-set", on_switch_state)
        self.pack_start(self.ipv6_row, False, False, 0)
