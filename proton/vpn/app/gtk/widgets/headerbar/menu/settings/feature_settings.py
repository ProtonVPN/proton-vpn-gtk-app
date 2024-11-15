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
from typing import TYPE_CHECKING

from gi.repository import Gtk, GObject
from proton.vpn.app.gtk.widgets.main.confirmation_dialog import ConfirmationDialog
from proton.vpn.core.settings import NetShield
from proton.vpn.app.gtk.controller import Controller
from proton.vpn.app.gtk.widgets.headerbar.menu.settings.common import (
    BaseCategoryContainer, ComboboxWidget, ToggleWidget, SettingName, SettingDescription
)
from proton.vpn.connection.enum import KillSwitchSetting as KillSwitchSettingEnum
from proton.vpn.app.gtk.widgets.headerbar.menu.settings.custom_dns import CustomDNSWidget

if TYPE_CHECKING:
    from proton.vpn.app.gtk.widgets.headerbar.menu.settings.settings_window import \
        SettingsWindow


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
    SWITCH_KILLSWITCH_IF_CONNECTION_ACTIVE_DESCRIPTION = "Kill switch selection "\
        "is disabled while VPN is active. Disconnect to make changes."

    def __init__(self, controller: Controller, settings_window: "SettingsWindow"):
        super().__init__(self.CATEGORY_NAME)
        self._controller = controller
        self._settings_window = settings_window
        self.netshield = None

    def build_ui(self):
        """Builds the UI, invoking all necessary methods that are
        under this category."""
        self.build_netshield()
        self.build_killswitch()
        self.build_port_forwarding()

    def build_netshield(self):
        """Builds and adds the `netshield` setting to the widget.
        It takes into consideration the `clientconfig` value and if
        the user has the expected `tier` to be used. If the user has a
        lower tier then required then an upgrade UI is displayed.
        """
        def on_combobox_changed(combobox: Gtk.ComboBoxText, combobox_widget: ComboboxWidget):
            model = combobox.get_model()
            treeiter = combobox.get_active_iter()
            netshield = int(model[treeiter][1])
            combobox_widget.save_setting(netshield)
            self._settings_window.notify_user_with_reconnect_message()
            self.emit("netshield-setting-changed", netshield)

        netshield_options = [
            (str(NetShield.NO_BLOCK), "Off"),
            (str(NetShield.BLOCK_MALICIOUS_URL), "Block Malware"),
            (str(NetShield.BLOCK_ADS_AND_TRACKING), "Block ads, trackers and malware"),
        ]
        self.netshield = ComboboxWidget(
            controller=self._controller,
            title=self.NETSHIELD_LABEL,
            description=self.NETSHIELD_DESCRIPTION,
            setting_name="settings.features.netshield",
            combobox_options=netshield_options,
            requires_subscription_to_be_active=True,
            callback=on_combobox_changed
        )
        self.pack_start(self.netshield, False, False, 0)

    def build_killswitch(self):
        """Builds and adds the `killswitch` setting to the widget."""
        killswitch = KillSwitchWidget.build(self._controller)
        self.pack_start(killswitch, False, False, 0)

    def build_port_forwarding(self):
        """Builds and adds the `port_forwarding` setting to the widget."""
        def on_switch_state(_, new_value: bool, toggle_widget: ToggleWidget):
            description_value = self.PORT_FORWARDING_DESCRIPTION
            if new_value:
                description_value = self.PORT_FORWARDING_SETUP_GUIDE

            toggle_widget.save_setting(new_value)
            toggle_widget.description.set_label(description_value)

            self._settings_window.notify_user_with_reconnect_message()

        port_forwarding_widget = ToggleWidget(
            controller=self._controller,
            title=self.PORT_FORWARDING_LABEL,
            description=self.PORT_FORWARDING_DESCRIPTION,
            setting_name="settings.features.port_forwarding",
            requires_subscription_to_be_active=True,
            callback=on_switch_state
        )
        if port_forwarding_widget.get_setting():
            port_forwarding_widget.description.set_label(self.PORT_FORWARDING_SETUP_GUIDE)

        self.pack_start(port_forwarding_widget, False, False, 0)

    @GObject.Signal(name="netshield-setting-changed", arg_types=(int,))
    def netshield_setting_changed(self, new_setting: int):
        """Signal emitted after a netshield setting is set."""

    def on_custom_dns_setting_changed(
        self, custom_dns_widget: CustomDNSWidget, new_setting: int
    ):
        """temp"""
        def _on_dialog_button_click(confirmation_dialog: ConfirmationDialog, response_type: int):
            enable_custom_dns = Gtk.ResponseType(response_type) == Gtk.ResponseType.YES
            if enable_custom_dns:
                self.netshield.off()
            else:
                # We need to reverse back the option here since gtk does not allow an easy way to
                # intercept changes before they happen.
                custom_dns_widget.off()

            confirmation_dialog.destroy()

        netshield_enabled = int(self.netshield.get_setting())
        if netshield_enabled == NetShield.NO_BLOCK or not new_setting:
            return

        dialog = ConfirmationDialog(
            message=self._build_dialog_content(),
            title="Enable Custom DNS",
            yes_text="_Enable", no_text="_Cancel"
        )
        dialog.set_default_size(400, 200)
        dialog.connect("response", _on_dialog_button_click)
        dialog.set_modal(True)
        dialog.set_transient_for(self._settings_window)
        dialog.show()

    def _build_dialog_content(self):
        container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        container.set_spacing(10)

        question = Gtk.Label(label="Enable Custom DNS ?")
        question.set_halign(Gtk.Align.START)

        clarification = Gtk.Label(label="This will disable Netshield.")
        clarification.set_halign(Gtk.Align.START)
        clarification.get_style_context().add_class("dim-label")

        # learn_more = Gtk.Label(
        #     label='<a href="https://protonvpn.com/support/custom-dns">Learn more</a>'
        # )
        # learn_more.set_halign(Gtk.Align.START)
        # learn_more.get_style_context().add_class("dim-label")
        # learn_more.set_use_markup(True)

        container.pack_start(question, False, False, 0)
        container.pack_start(clarification, False, False, 0)
        # container.pack_start(learn_more, False, False, 0)

        return container
