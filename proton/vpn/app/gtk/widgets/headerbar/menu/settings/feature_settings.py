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
from typing import TYPE_CHECKING, Optional

from gi.repository import Gtk, GObject
from proton.vpn.app.gtk.widgets.main.confirmation_dialog import ConfirmationDialog
from proton.vpn.core.settings import NetShield
from proton.vpn.app.gtk.controller import Controller
from proton.vpn.app.gtk.utils.safe_signal_connect import safe_signal_connect
from proton.vpn.app.gtk.widgets.headerbar.menu.settings.common import (
    BaseCategoryContainer, ComboboxWidget, ToggleWidget,
    ReactiveSettingContainer
)
from proton.vpn.app.gtk.widgets.headerbar.menu.settings.custom_dns import CustomDNSWidget
from proton.vpn.app.gtk.widgets.headerbar.menu.settings.kill_switch import KillSwitchWidget
from proton.vpn.app.gtk.widgets.headerbar.menu.settings.split_tunneling import SplitTunnelingToggle

if TYPE_CHECKING:
    from proton.vpn.app.gtk.widgets.headerbar.menu.settings.settings_window import \
        SettingsWindow


class FeatureSettings(BaseCategoryContainer, ReactiveSettingContainer):  # noqa: E501 # pylint: disable=line-too-long, too-many-instance-attributes
    """Settings related to connection are all grouped under this class."""
    CATEGORY_NAME = "Features"
    NETSHIELD_LABEL = "NetShield"
    NETSHIELD_DESCRIPTION = "Protect yourself from ads, malware, and trackers "\
        "on websites and apps."
    PORT_FORWARDING_LABEL = "Port forwarding"
    PORT_FORWARDING_DESCRIPTION_LEARN_MORE = "Bypass firewalls to connect to P2P servers "\
        "and devices on your local network. "\
        "<a href=\"https://protonvpn.com/support/port-forwarding/#linux\">Learn more</a>"
    SWITCH_KILLSWITCH_IF_CONNECTION_ACTIVE_DESCRIPTION = "Kill switch selection "\
        "is disabled while VPN is active. Disconnect to make changes."

    def __init__(self, controller: Controller, settings_window: "SettingsWindow"):
        super().__init__(self.CATEGORY_NAME)
        self._controller = controller
        self._settings_window = settings_window
        self.netshield: Optional[ComboboxWidget] = None
        self.killswitch: Optional[KillSwitchWidget] = None
        self.port_forwarding: Optional[ToggleWidget] = None
        self.split_tunneling: Optional[SplitTunnelingToggle] = None
        self._conflict_custom_dns_widget: Optional[CustomDNSWidget] = None

    def build_ui(self):
        """Builds the UI, invoking all necessary methods that are
        under this category."""
        self.build_netshield()
        self.build_killswitch()
        self.build_port_forwarding()
        if self._controller.split_tunneling_available:
            self.build_split_tunneling()

    def build_netshield(self):
        """Builds and adds the `netshield` setting to the widget.
        It takes into consideration the `clientconfig` value and if
        the user has the expected `tier` to be used. If the user has a
        lower tier then required then an upgrade UI is displayed.
        """
        netshield_options = [
            (str(NetShield.NO_BLOCK.value), "Off"),
            (str(NetShield.BLOCK_MALICIOUS_URL.value), "Block Malware"),
            (str(NetShield.BLOCK_ADS_AND_TRACKING.value), "Block ads, trackers and malware"),
        ]
        self.netshield = ComboboxWidget(
            controller=self._controller,
            title=self.NETSHIELD_LABEL,
            description=self.NETSHIELD_DESCRIPTION,
            setting_name="settings.features.netshield",
            combobox_options=netshield_options,
            requires_subscription_to_be_active=True,
            callback=self._on_netshield_combobox_changed
        )
        self.append(self.netshield)

    def _on_netshield_combobox_changed(self, combobox: Gtk.ComboBoxText):
        model = combobox.get_model()
        treeiter = combobox.get_active_iter()
        netshield = int(model[treeiter][1])
        self.netshield.save_setting(netshield)
        self.emit("netshield-setting-changed", netshield)

    def build_killswitch(self):
        """Builds and adds the `killswitch` setting to the widget."""
        self.killswitch = KillSwitchWidget.build(self._controller)
        self.append(self.killswitch)

    def build_port_forwarding(self):
        """Builds and adds the `port_forwarding` setting to the widget."""

        self.port_forwarding = ToggleWidget(
            controller=self._controller,
            title=self.PORT_FORWARDING_LABEL,
            description=self.PORT_FORWARDING_DESCRIPTION_LEARN_MORE,
            setting_name="settings.features.port_forwarding",
            requires_subscription_to_be_active=True
        )

        self.append(self.port_forwarding)

    @GObject.Signal(name="netshield-setting-changed", arg_types=(int,))
    def netshield_setting_changed(self, custom_dns_enabled: int):
        """Signal emitted after a netshield setting is set."""

    def _on_dialog_button_click(
        self,
        confirmation_dialog: ConfirmationDialog,
        response_type: int
    ):
        if not self._conflict_custom_dns_widget:
            return

        enable_custom_dns = Gtk.ResponseType(response_type) == Gtk.ResponseType.YES
        if enable_custom_dns:
            self.netshield.off()
            self._settings_window.notify_user_with_reconnect_message()
        else:
            # We need to reverse back the option here since gtk does not allow an easy way to
            # intercept changes before they happen.
            self._conflict_custom_dns_widget.off()

        self._conflict_custom_dns_widget = None
        confirmation_dialog.destroy()

    def on_custom_dns_setting_changed(
        self,
        custom_dns_widget: CustomDNSWidget,
        custom_dns_enabled: int
    ):
        """Called on custom DNS setting change (conflict resolution)"""
        netshield_disabled = (
            int(self.netshield.get_setting()) == NetShield.NO_BLOCK
        )

        if not custom_dns_enabled or netshield_disabled:
            self._settings_window.notify_user_with_reconnect_message(
                only_notify_on_active_connection=True
            )
            return

        self._conflict_custom_dns_widget = custom_dns_widget

        dialog = ConfirmationDialog(
            message=self._build_dialog_content(),
            title="Enable Custom DNS",
            yes_text="_Enable", no_text="_Cancel"
        )
        dialog.set_default_size(400, 200)
        safe_signal_connect(dialog, "response", self._on_dialog_button_click)
        dialog.set_modal(True)
        dialog.set_transient_for(self._settings_window)
        dialog.present()

    def _build_dialog_content(self):
        container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        container.set_spacing(10)

        question = Gtk.Label(label="Enable Custom DNS ?")
        question.set_halign(Gtk.Align.START)

        clarification = Gtk.Label(label="This will disable Netshield.")
        clarification.set_halign(Gtk.Align.START)
        clarification.add_css_class("dim-label")

        learn_more = Gtk.Label(
            label='<a href="https://protonvpn.com/support/custom-dns#netshield">Learn more</a>'
        )
        learn_more.set_halign(Gtk.Align.START)
        learn_more.add_css_class("dim-label")
        learn_more.set_use_markup(True)

        container.append(question)
        container.append(clarification)
        container.append(learn_more)

        return container

    def build_split_tunneling(self):
        """Build split tunneling UI.
        """
        self.split_tunneling = SplitTunnelingToggle.build(self._controller)
        self.append(self.split_tunneling)
