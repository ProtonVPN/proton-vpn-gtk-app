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
from proton.vpn.core_api.settings import NetShield
from proton.vpn.app.gtk.controller import Controller
from proton.vpn.app.gtk.widgets.main.notification_bar import NotificationBar
from proton.vpn.app.gtk.widgets.headerbar.menu.settings.common import (
    RECONNECT_MESSAGE, CategoryHeader, SettingRow, SettingName, SettingDescription
)


class FeatureSettings(Gtk.Box):  # pylint: disable=too-many-instance-attributes
    """Settings related to connection are all grouped under this class."""
    CATEGORY_NAME = "Features"
    NETSHIELD_LABEL = "NetShield"
    NETSHIELD_DESCRIPTION = "Protect yourself from ads, malware, and trackers "\
        "on websites and apps."
    PORT_FORWARDING_LABEL = "Port Forwarding"
    PORT_FORWARDING_DESCRIPTION = "Bypass firewalls to connect to P2P servers "\
        "and devices on your local network."
    PORT_FORWARDING_SETUP_GUIDE = "Follow our "\
        "<a href=\"https://protonvpn.com/support/port-forwarding-manual-setup/"\
        "#how-to-use-port-forwarding\">guide</a>"\
        " to set it up."

    def __init__(self, controller: Controller, notification_bar: NotificationBar):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self._controller = controller
        self._notification_bar = notification_bar

        self.netshield_row = None
        self.port_forwarding_row = None

        self.set_halign(Gtk.Align.FILL)
        self.set_spacing(15)

        self.get_style_context().add_class("setting-category")

    def build_ui(self):
        """Builds the UI, invoking all necessary methods that are
        under this category."""
        self.pack_start(CategoryHeader(self.CATEGORY_NAME), False, False, 0)
        self.build_netshield()
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
        combobox.set_hexpand(True)
        combobox.set_halign(Gtk.Align.END)

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
        switch.set_halign(Gtk.Align.END)
        switch.set_hexpand(True)

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
