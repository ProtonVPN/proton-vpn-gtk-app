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

from proton.vpn.app.gtk.controller import Controller
from proton.vpn.app.gtk.widgets.headerbar.menu.settings.common import (
    BaseCategoryContainer, ToggleWidget, ComboboxWidget
)

if TYPE_CHECKING:
    from proton.vpn.app.gtk.widgets.headerbar.menu.settings.settings_window import \
        SettingsWindow


class ConnectionSettings(BaseCategoryContainer):  # pylint: disable=too-many-instance-attributes
    """Settings related to connection are all grouped under this class."""
    CATEGORY_NAME = "Connection"
    PROTOCOL_LABEL = "Protocol"
    PROTOCOL_DESCRIPTION = "Protocol can only be changed when VPN is disconnected."
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
        self._settings_window = settings_window

    def build_ui(self):
        """Builds the UI, invoking all necessary methods that are
        under this category."""
        self.build_protocol()
        self.build_vpn_accelerator()
        self.build_moderate_nat()
        if self._controller.feature_flags.get("IPv6Support"):
            self.build_ipv6()

    def build_protocol(self):
        """Builds and adds the `protocol` setting to the widget."""
        protocol_list_of_tuples = [
            (protocol.cls.protocol, protocol.cls.ui_protocol)
            for protocol in self._controller.get_available_protocols()
        ]

        self.pack_start(ComboboxWidget(
                controller=self._controller,
                title=self.PROTOCOL_LABEL,
                description=self.PROTOCOL_DESCRIPTION,
                setting_name="settings.protocol",
                combobox_options=protocol_list_of_tuples,
                disable_on_active_connection=True
        ), False, False, 0)

    def build_vpn_accelerator(self):
        """Builds and adds the `vpn_accelerator` setting to the widget."""
        def on_switch_state(_, new_value: bool, toggle_widget: ToggleWidget):
            toggle_widget.save_setting(new_value)
            self._settings_window.notify_user_with_reconnect_message()

        self.pack_start(ToggleWidget(
            controller=self._controller,
            title=self.VPN_ACCELERATOR_LABEL,
            description=self.VPN_ACCELERATOR_DESCRIPTION,
            setting_name="settings.features.vpn_accelerator",
            requires_subscription_to_be_active=True,
            callback=on_switch_state
        ), False, False, 0)

    def build_moderate_nat(self):
        """Builds and adds the `moderate_nat` setting to the widget."""
        def on_switch_state(_, new_value: bool, toggle_widget: ToggleWidget):
            toggle_widget.save_setting(new_value)
            self._settings_window.notify_user_with_reconnect_message()

        self.pack_start(ToggleWidget(
            controller=self._controller,
            title=self.MODERATE_NAT_LABEL,
            description=self.MODERATE_NAT_DESCRIPTION,
            setting_name="settings.features.moderate_nat",
            requires_subscription_to_be_active=True,
            callback=on_switch_state
        ), False, False, 0)

    def build_ipv6(self):
        """Builds and adds the `ipv6` setting to the widget."""
        def on_switch_state(_, new_value: bool, toggle_widget: ToggleWidget):
            toggle_widget.save_setting(new_value)
            self._settings_window.notify_user_with_reconnect_message(force_notify=True)

        self.pack_start(ToggleWidget(
            controller=self._controller,
            title=self.IPV6_LABEL,
            description=self.IPV6_DESCRIPTION,
            setting_name="settings.ipv6",
            callback=on_switch_state
        ), False, False, 0)
