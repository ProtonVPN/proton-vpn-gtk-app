"""
This module contains custom DNS objects.


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
from types import ModuleType
from typing import List, TYPE_CHECKING, Optional, cast
from contextlib import contextmanager

from gi.repository import Gtk, GObject
from proton.vpn.app.gtk.controller import Controller
from proton.vpn.app.gtk.utils.safe_signal_connect import safe_signal_connect
from proton.vpn.app.gtk.widgets.main.confirmation_dialog import ConfirmationDialog
from proton.vpn.core.settings import CustomDNSEntry, NetShield
from proton.vpn.app.gtk.widgets.headerbar.menu.settings.common import ToggleWidget


if TYPE_CHECKING:
    from proton.vpn.app.gtk.widgets.headerbar.menu.settings.feature_settings import \
        FeatureSettings
    from proton.vpn.app.gtk.widgets.headerbar.menu.settings.settings_window import \
        SettingsWindow


class CustomDNSRow(Gtk.Box):  # pylint: disable=too-few-public-methods
    """A simple row that contains the label of the DNS server and a button to
    make it easily removable."""
    def __init__(self, custom_dns_entry: CustomDNSEntry, gtk: Optional[ModuleType] = None):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL)
        self.gtk = gtk or Gtk
        self.custom_dns_entry = custom_dns_entry
        ip_label = self.gtk.Label(label=custom_dns_entry.convert_ip_to_short_format())
        ip_label.set_hexpand(True)  # Make label expand to push button to the right
        ip_label.set_halign(self.gtk.Align.START)  # Keep label left-aligned
        self.button = self.gtk.Button.new_from_icon_name("edit-delete-symbolic")
        self.append(ip_label)
        self.append(self.button)


class CustomDNSList(Gtk.Box):  # pylint: disable=too-few-public-methods
    """Hold a list of CustomDNSRow objects.

    It also takes care of reading from and saving to the settings file.
    Nowhere else is the settings file modified, in regards to custom dns setting.
    """

    def __init__(self, ip_list: List[CustomDNSEntry]):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.set_spacing(5)

        for custom_dns in ip_list:
            custom_dns_row = CustomDNSRow(custom_dns)
            safe_signal_connect(custom_dns_row.button, "clicked", self._on_dns_delete_clicked)
            self.append(custom_dns_row)

    @GObject.Signal(name="dns-ip-removed", arg_types=(object,))
    def dns_ip_removed(self, custom_dns_entry: CustomDNSEntry):
        """Signal emitted after a dns IP is removed from the list."""

    def add_dns(self, new_dns: CustomDNSEntry):
        """Add a new DNS entry to the list"""
        custom_dns_row = CustomDNSRow(new_dns)
        safe_signal_connect(custom_dns_row.button, "clicked", self._on_dns_delete_clicked)
        self.append(custom_dns_row)

    def _on_dns_delete_clicked(self, button: Gtk.Button):
        parent_widget = cast(CustomDNSRow, button.get_parent())
        self.remove(parent_widget)
        self.emit("dns-ip-removed", parent_widget.custom_dns_entry)


class CustomDNSManager(Gtk.Box):  # pylint: disable=too-few-public-methods
    """Serves as a container for everything related to management of custom DNS entries."""
    SETTING_NAME = "settings.custom_dns.ip_list"
    INVALID_IP_ERROR_MESSAGE = "Enter a valid IPv4 or IPv6 address"

    def __init__(
        self,
        controller: Controller,
        gtk: Optional[ModuleType] = None,
        custom_dns_list: Optional[CustomDNSList] = None
    ):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.set_spacing(15)

        self.gtk = gtk or Gtk
        self._controller = controller

        label = self.gtk.Label(label="Add new server")
        label.set_halign(Gtk.Align.START)

        self._error_message_revealer = self._build_error_message()
        entry_row = self._build_entry_row()
        with self._get_ip_list() as ip_list:
            self._custom_dns_list = custom_dns_list or CustomDNSList(ip_list)

        safe_signal_connect(
            self._custom_dns_list, "dns-ip-removed", self._on_dns_delete_clicked
        )

        self.append(label)
        self.append(entry_row)
        self.append(self._error_message_revealer)
        self.append(self._custom_dns_list)

    def _build_entry_row(self) -> Gtk.Grid:
        row = self.gtk.Grid(orientation=Gtk.Orientation.HORIZONTAL)
        row.set_column_spacing(10)

        self._dns_entry: Gtk.Entry = self.gtk.Entry()
        self._dns_entry.set_hexpand(True)
        self._dns_entry.set_halign(Gtk.Align.FILL)

        self._add_button: Gtk.Button = self.gtk.Button(label="Add")
        safe_signal_connect(self._add_button, "clicked", self._on_dns_add_clicked)

        row.attach(self._dns_entry, 0, 0, 1, 1)
        row.attach(self._add_button, 1, 0, 1, 1)

        return row

    def _build_error_message(self):
        revealer = self.gtk.Revealer()
        error_label = self.gtk.Label()
        error_label.set_halign(Gtk.Align.START)
        error_label.add_css_class("signal-danger")
        revealer.set_child(error_label)
        revealer.set_reveal_child(False)

        return revealer

    def _on_dns_add_clicked(
        self, _: Gtk.Button
    ):
        if self._error_message_revealer.get_reveal_child():
            self._error_message_revealer.set_reveal_child(False)

        string_from_entry = self._dns_entry.get_text().lower().strip()

        try:
            new_custom_dns_entry = CustomDNSEntry.new_from_string(string_from_entry)
        except ValueError:
            self._notify_user_of_invalid_dns_entry(self._error_message_revealer)
            return

        self._add_dns(new_custom_dns_entry)
        self._dns_entry.set_text("")

    def _add_dns(self, new_custom_dns_entry: CustomDNSEntry):
        with self._edit_ip_list() as ip_list:
            ip_list.append(new_custom_dns_entry)

        self._custom_dns_list.add_dns(new_custom_dns_entry)

    def _on_dns_delete_clicked(self, _: CustomDNSList, existing_dns_ip_entry: CustomDNSEntry):
        with self._edit_ip_list() as ip_list:
            ip_list.remove(existing_dns_ip_entry)

    def _notify_user_of_invalid_dns_entry(self, error_message_revealer: Gtk.Revealer):
        child = error_message_revealer.get_child()
        child.set_label(self.INVALID_IP_ERROR_MESSAGE)
        error_message_revealer.set_reveal_child(True)

    @contextmanager
    def _get_ip_list(self):
        """Helper method to view the ip list."""
        yield self._controller.get_setting_attr(CustomDNSManager.SETTING_NAME)

    @contextmanager
    def _edit_ip_list(self):
        """Helper method to edit the ip list and save it."""
        ip_list = self._controller.get_setting_attr(CustomDNSManager.SETTING_NAME)
        yield ip_list
        self._controller.save_setting_attr(CustomDNSManager.SETTING_NAME, ip_list)

    def set_entry_text(self, new_value: str):
        """Simulate typing content to entry."""
        self._dns_entry.set_text(new_value)

    def add_button_click(self):
        """Simulate add button click"""
        self._add_button.emit("clicked")


class CustomDNSWidget(ToggleWidget):
    """Custom DNS widget.

    Handles everything from the toggle, to revealing and displaying the
    custom DNS IPs.
    """
    LABEL = "Custom DNS servers"
    DESCRIPTION = "Connect to Proton VPN using your own domain name servers (DNS)."
    SETTING_NAME = "settings.custom_dns.enabled"

    def __init__(
        self, controller: Controller, settings_window: Gtk.Window,
        gtk: Optional[ModuleType] = None
    ):
        super().__init__(
            controller=controller,
            title=self.LABEL,
            description=self.DESCRIPTION,
            setting_name=self.SETTING_NAME,
            requires_subscription_to_be_active=True,
            callback=self._on_switch_button_toggle,
        )

        self.gtk = gtk or Gtk
        self._controller = controller
        self.revealer: Optional[Gtk.Revealer] = None
        self._custom_dns_manager: Optional[CustomDNSManager] = None
        self._settings_window = settings_window
        self._conflict_feature_settings = None

    @staticmethod
    def build(controller: Controller, settings_window: "SettingsWindow") -> "CustomDNSWidget":
        """Shortcut method to initialize widget."""
        widget = CustomDNSWidget(controller, settings_window)
        widget.build_revealer()
        return widget

    def build_revealer(self):
        """Builds the revealer"""
        self.revealer = self.gtk.Revealer()
        self.attach(self.revealer, 0, 2, 2, 1)
        revealer_container = self._build_revealer_container()
        self.revealer.set_child(revealer_container)
        self.revealer.set_reveal_child(self.get_setting())

    def _build_revealer_container(self) -> Gtk.Box:
        self._custom_dns_manager = CustomDNSManager(self._controller)
        return self._custom_dns_manager

    def _on_switch_button_toggle(self, _, new_value: bool, __):
        self.revealer.set_reveal_child(new_value)
        self.save_setting(new_value)
        self.emit("custom-dns-setting-changed", new_value)

    @GObject.Signal(name="custom-dns-setting-changed", arg_types=(bool,))
    def custom_dns_setting_changed(self, new_setting: bool):
        """Signal emitted after a custom DNS setting is set."""

    def _on_dialog_button_click(
        self,
        confirmation_dialog: ConfirmationDialog,
        response_type: int
    ):
        enable_netshield = Gtk.ResponseType(response_type) == Gtk.ResponseType.YES
        if enable_netshield:
            self.off()
        else:
            # We need to reverse back the option here since gtk does not allow an easy way to
            # intercept changes before they happen.
            self._conflict_feature_settings.netshield.off()

        self._conflict_feature_settings = None
        confirmation_dialog.destroy()

    def on_netshield_setting_changed(
        self,
        feature_settings: "FeatureSettings",
        new_setting: int
    ):
        """Called on netshield setting change (conflict resolution)"""
        custom_dns_enabled = self.get_setting()
        netshield_disabled = new_setting == NetShield.NO_BLOCK

        if not custom_dns_enabled or netshield_disabled:
            return

        self._conflict_feature_settings = feature_settings
        dialog = ConfirmationDialog(
            message=self._build_dialog_content(),
            title="Enable Netshield",
            yes_text="_Enable", no_text="_Cancel"
        )
        #  pylint: disable=duplicate-code
        dialog.set_default_size(400, 200)
        safe_signal_connect(dialog, "response", self._on_dialog_button_click)
        dialog.set_modal(True)
        dialog.set_transient_for(self._settings_window)
        dialog.present()

    def _build_dialog_content(self):
        #  pylint: disable=duplicate-code
        container = self.gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        container.set_spacing(10)

        question = self.gtk.Label(label="Enable Netshield ?")
        question.set_halign(Gtk.Align.START)

        clarification = self.gtk.Label(label="This will disable custom DNS.")
        clarification.set_halign(Gtk.Align.START)
        clarification.add_css_class("dim-label")

        learn_more = self.gtk.Label(
            label='<a href="https://protonvpn.com/support/custom-dns#netshield">Learn more</a>'
        )
        learn_more.set_halign(Gtk.Align.START)
        learn_more.add_css_class("dim-label")
        learn_more.set_use_markup(True)

        container.append(question)
        container.append(clarification)
        container.append(learn_more)

        return container
