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

from proton.vpn.app.gtk.conflicts import WIREGUARD_PROTOCOL

from proton.vpn.app.gtk.controller import Controller
from proton.vpn.app.gtk.utils.safe_signal_connect import safe_signal_connect
from proton.vpn.app.gtk.widgets.headerbar.menu.settings.common import (
    BaseCategoryContainer, BetaTag, ToggleWidget, ConflictableComboboxWidget,
    ReactiveSettingContainer, ReactiveSetting
)
from proton.vpn.app.gtk.widgets.headerbar.menu.settings.custom_dns import CustomDNSWidget

if TYPE_CHECKING:
    from proton.vpn.app.gtk.widgets.headerbar.menu.settings.settings_window import \
        SettingsWindow


class ProtocolComboboxWidget(ConflictableComboboxWidget, ReactiveSetting):
    """Combobox widget for selecting the VPN protocol."""

    PROTUN_CHECKBOX_LABEL = "Use Proton protocols"

    PROTUN_PROTOCOL_GROUP = "protun"
    GENERIC_PROTOCOL_GROUP = "generic"

    def on_settings_changed(self, settings):
        """
        When settings are changed, we need to check if the protocol is
        still valid and update the combobox accordingly.
        """
        if self.combobox.get_active_text() != settings.protocol:
            self.combobox.set_active_id(settings.protocol)

    def get_protun_protocols(self) -> list[str]:
        """
        Returns the list of protun protocols if the feature flag is enabled,
        otherwise returns an empty list. We can use this method to determine
        whether the protun protocols should be shown in the UI or not.
        """
        # is_protun_enabled = self._controller.feature_flags.get("ProTunV1")
        is_protun_enabled = True
        if is_protun_enabled:
            return self._controller.get_available_protocols(self.PROTUN_PROTOCOL_GROUP)
        return []

    def protocol_group(self, current_protocol: str, protun_protocols: list) -> str:
        """Returns the protocol group for the given protocol."""
        for protocol in protun_protocols:
            if str(protocol.protocol) == current_protocol:
                return self.PROTUN_PROTOCOL_GROUP
        return self.GENERIC_PROTOCOL_GROUP

    def _build_ui(self):
        super()._build_ui()

        current_protocol = self.get_setting()
        protun_protocols = self.get_protun_protocols()

        if protun_protocols:
            current_protocol_group = self.protocol_group(current_protocol, protun_protocols)
            self._build_protun_checkbox(current_protocol_group)
        else:
            current_protocol_group = self.GENERIC_PROTOCOL_GROUP

        current_protocols = self._controller.get_available_protocols(current_protocol_group)
        self._repopulate_combobox(current_protocols)

        with self.pause_callback():
            self.combobox.set_active_id(current_protocol)

    def _build_protun_checkbox(self, current_protocol_group):
        """Builds and attaches the protun checkbox, initialising it from the current setting."""
        is_protun = current_protocol_group == self.PROTUN_PROTOCOL_GROUP

        protun_checkbox = Gtk.CheckButton(label=self.PROTUN_CHECKBOX_LABEL)
        protun_checkbox.set_active(is_protun)
        safe_signal_connect(protun_checkbox, "toggled", self._on_protun_checkbox_toggled)

        checkbox_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        checkbox_row.append(protun_checkbox)
        checkbox_row.append(BetaTag())
        self.attach(checkbox_row, 0, 2, 2, 1)

    def _repopulate_combobox(self, protocols):
        """Repopulates the combobox with the given protocols."""
        with self.pause_callback():
            self.combobox.set_entry_text_column(0)
            self.combobox.remove_all()
            for protocol in protocols:
                self.combobox.append(str(protocol.protocol), protocol.ui_protocol)
            self.combobox.set_entry_text_column(1)

    def _on_protun_checkbox_toggled(self, checkbox):
        if checkbox.get_active():
            protocol_group = self.PROTUN_PROTOCOL_GROUP
        else:
            protocol_group = self.GENERIC_PROTOCOL_GROUP
        protocols = self._controller.get_available_protocols(protocol_group)
        self._repopulate_combobox(protocols)
        if protocols:
            self.combobox.set_active(0)


class ConnectionSettings(BaseCategoryContainer, ReactiveSettingContainer):  # noqa: E501 # pylint: disable=line-too-long, too-many-instance-attributes
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
        self.custom_dns = None
        self._protocol_widget = None
        self._vpn_accelerator_toggle = None
        self._moderate_nat_toggle = None
        self._ipv6_toggle = None

    def build_ui(self):
        """Builds the UI, invoking all necessary methods that are
        under this category."""
        self.build_protocol()
        self.build_vpn_accelerator()
        self.build_moderate_nat()
        self.build_ipv6()
        self.build_custom_dns()

    def build_protocol(self):
        """Builds and adds the `protocol` setting to the widget."""
        def do_set(combobox, new_value: str):
            combobox.save_setting(new_value)

        def do_revert(combobox):
            combobox.combobox.set_active_id(WIREGUARD_PROTOCOL)

        self._protocol_widget = ProtocolComboboxWidget(
            controller=self._controller,
            title=self.PROTOCOL_LABEL,
            description=self.PROTOCOL_DESCRIPTION,
            setting_name="settings.protocol",
            combobox_options=[],
            disable_on_active_connection=True,
            do_set=do_set,
            do_revert=do_revert
        )
        self.append(self._protocol_widget)

    def build_vpn_accelerator(self):
        """Builds and adds the `vpn_accelerator` setting to the widget."""
        def on_switch_state(_, new_value: bool, toggle_widget: ToggleWidget):
            toggle_widget.save_setting(new_value)

        self._vpn_accelerator_toggle = ToggleWidget(
            controller=self._controller,
            title=self.VPN_ACCELERATOR_LABEL,
            description=self.VPN_ACCELERATOR_DESCRIPTION,
            setting_name="settings.features.vpn_accelerator",
            requires_subscription_to_be_active=True,
            callback=on_switch_state
        )
        self.append(self._vpn_accelerator_toggle)

    def build_moderate_nat(self):
        """Builds and adds the `moderate_nat` setting to the widget."""
        def on_switch_state(_, new_value: bool, toggle_widget: ToggleWidget):
            toggle_widget.save_setting(new_value)

        self._moderate_nat_toggle = ToggleWidget(
            controller=self._controller,
            title=self.MODERATE_NAT_LABEL,
            description=self.MODERATE_NAT_DESCRIPTION,
            setting_name="settings.features.moderate_nat",
            requires_subscription_to_be_active=True,
            callback=on_switch_state
        )
        self.append(self._moderate_nat_toggle)

    def build_ipv6(self):
        """Builds and adds the `ipv6` setting to the widget."""
        def on_switch_state(_, new_value: bool, toggle_widget: ToggleWidget):
            toggle_widget.save_setting(new_value)
            self._settings_window.notify_user_with_reconnect_message(force_notify=True)

        self._ipv6_toggle = ToggleWidget(
            controller=self._controller,
            title=self.IPV6_LABEL,
            description=self.IPV6_DESCRIPTION,
            setting_name="settings.ipv6",
            callback=on_switch_state
        )
        self.append(self._ipv6_toggle)

    def build_custom_dns(self):
        """Builds and adds the `custom_dns` setting to the widget."""
        self.custom_dns = CustomDNSWidget.build(self._controller, self._settings_window)
        self.append(self.custom_dns)
