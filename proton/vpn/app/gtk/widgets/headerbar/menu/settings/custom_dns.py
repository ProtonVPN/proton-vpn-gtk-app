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
from typing import List
from contextlib import contextmanager
import ipaddress

from gi.repository import Gtk, GObject
from proton.vpn.app.gtk.controller import Controller
from proton.vpn.app.gtk.widgets.headerbar.menu.settings.common import (
    ToggleWidget, save_setting, get_setting
)


class CustomDNSRow(Gtk.Box):  # pylint: disable=too-few-public-methods
    """A simple row that contains the label of the DNS server and a button to
    make it easily removable."""
    def __init__(self, dns_ip: str, gtk: Gtk = None):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL)
        self.gtk = gtk or Gtk
        ip_label = self.gtk.Label(label=dns_ip)
        self.button = self.gtk.Button.new_from_icon_name("window-close", 1)
        self.pack_start(ip_label, False, False, 0)
        self.pack_end(self.button, False, False, 0)

    @property
    def ip(self) -> str:  # pylint: disable=invalid-name
        """Returns the stored IP in the label."""
        return self.get_children()[0].get_label()


class CustomDNSList(Gtk.Box):  # pylint: disable=too-few-public-methods
    """Hold a list of CustomDNSRow objects.

    It also takes care of reading from and saving to the settings file.
    Nowhere else is the settings file modified, in regards to custom dns setting.
    """

    def __init__(self, ip_list: List[str]):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.set_spacing(5)

        for custom_dns in ip_list:
            custom_dns_row = CustomDNSRow(custom_dns)
            custom_dns_row.button.connect("clicked", self._on_dns_delete_clicked)
            self.pack_start(custom_dns_row, False, False, 0)

    @GObject.Signal(name="dns-ip-removed", arg_types=(str,))
    def dns_ip_removed(self, ip: str):  # pylint: disable=invalid-name
        """Signal emitted after a dns IP is removed from the list."""

    def add_ip(self, new_dns: str):
        """Add a new DNS entry to the list"""
        custom_dns_row = CustomDNSRow(new_dns)
        custom_dns_row.button.connect("clicked", self._on_dns_delete_clicked)
        custom_dns_row.show_all()
        self.pack_start(custom_dns_row, False, False, 0)

    def _on_dns_delete_clicked(self, button: Gtk.Button):
        parent_widget = button.get_parent()
        self.remove(parent_widget)
        self.emit("dns-ip-removed", parent_widget.ip)


class CustomDNSManager(Gtk.Box):  # pylint: disable=too-few-public-methods
    """Serves as a container for everything related to management of custom DNS entries."""
    SETTING_NAME = "settings.custom_dns_ips"
    DNS_LIMIT = 3
    INVALID_IP_ERROR_MESSAGE = "Enter a valid IPv4 or IPv6 address"

    def __init__(
        self,
        controller: Controller,
        gtk: Gtk = None,
        custom_dns_list: CustomDNSList = None
    ):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.set_spacing(15)

        self.gtk = gtk or Gtk
        self._controller = controller

        self._dns_entry = None
        self._add_button = None

        label = self.gtk.Label(label="Add new server")
        label.set_halign(Gtk.Align.START)

        error_message_revealer = self._build_error_message()
        entry_row = self._build_entry_row(error_message_revealer)
        with self._get_ip_list() as ip_list:
            self._custom_dns_list = custom_dns_list or CustomDNSList(ip_list)

        self._custom_dns_list.connect("dns-ip-removed", self._on_dns_delete_clicked)

        self.pack_start(label, False, False, 0)
        self.pack_start(entry_row, False, False, 0)
        self.pack_start(error_message_revealer, False, False, 0)
        self.pack_start(self._custom_dns_list, False, False, 0)

        self._ensure_user_can_still_add()

    def _build_entry_row(self, error_message_revealer: Gtk.Revealer) -> Gtk.Grid:
        row = self.gtk.Grid(orientation=Gtk.Orientation.HORIZONTAL)
        row.set_column_spacing(10)

        self._dns_entry = self.gtk.Entry()
        self._dns_entry.set_hexpand(True)
        self._dns_entry.set_halign(Gtk.Align.FILL)

        self._add_button = self.gtk.Button(label="Add")
        self._add_button.connect("clicked", self._on_dns_add_clicked, error_message_revealer)

        row.attach(self._dns_entry, 0, 0, 1, 1)
        row.attach(self._add_button, 1, 0, 1, 1)

        return row

    def _build_error_message(self):
        revealer = self.gtk.Revealer()
        error_label = self.gtk.Label()
        error_label.set_halign(Gtk.Align.START)
        error_label.get_style_context().add_class("signal-danger")
        revealer.add(error_label)
        revealer.set_reveal_child(False)

        return revealer

    def _on_dns_add_clicked(
        self, _: Gtk.Button, error_message_revealer: Gtk.Revealer
    ):
        if error_message_revealer.get_reveal_child():
            error_message_revealer.set_reveal_child(False)

        string_from_entry = self._dns_entry.get_text().lower().strip()

        try:
            addr = ipaddress.ip_address(string_from_entry)
        except ValueError:
            self._notify_user_of_invalid_dns_entry(error_message_revealer)
            return

        ip_in_string_type = addr.exploded

        self._add_dns(ip_in_string_type)
        self._dns_entry.set_text("")

    def _add_dns(self, new_dns_ip: str):
        with self._edit_ip_list() as ip_list:
            ip_list.append(new_dns_ip)

        self._custom_dns_list.add_ip(new_dns_ip)
        self._ensure_user_can_still_add()

    def _on_dns_delete_clicked(self, _: CustomDNSList, existing_dns_ip: str):
        with self._edit_ip_list() as ip_list:
            ip_list.remove(existing_dns_ip)

        self._ensure_user_can_still_add()

    def _notify_user_of_invalid_dns_entry(self, error_message_revealer: Gtk.Revealer):
        error_message_revealer.get_children()[0].set_label(self.INVALID_IP_ERROR_MESSAGE)
        error_message_revealer.set_reveal_child(True)

    def _ensure_user_can_still_add(self):
        self._ui_enabled = self._allow_to_add_more

    @property
    def _allow_to_add_more(self) -> bool:
        with self._get_ip_list() as ip_list:
            return bool(len(ip_list) < CustomDNSManager.DNS_LIMIT)

    @property
    def _ui_enabled(self) -> bool:
        return bool(
            self._dns_entry.get_sensitive()
            and self._add_button.get_sensitive()
        )

    @_ui_enabled.setter
    def _ui_enabled(self, new_value: bool):
        if self._ui_enabled and new_value or not self._ui_enabled and not new_value:
            return

        self._dns_entry.set_sensitive(new_value)
        self._add_button.set_sensitive(new_value)

    @contextmanager
    def _get_ip_list(self):
        """Helper method to view the ip list."""
        yield get_setting(self._controller, CustomDNSManager.SETTING_NAME)

    @contextmanager
    def _edit_ip_list(self):
        """Helper method to edit the ip list and save it."""
        ip_list = get_setting(self._controller, CustomDNSManager.SETTING_NAME)
        yield ip_list
        save_setting(self._controller, CustomDNSManager.SETTING_NAME, ip_list)

    def set_entry_text(self, new_value: str):
        """Simulate typing content to entry."""
        self._dns_entry.set_text(new_value)

    def add_button_click(self):
        """Simulate add button click"""
        self._add_button.clicked()


class CustomDNSWidget(ToggleWidget):
    """Custom DNS widget.

    Handles everything from the toggle, to revealing and displaying the
    custom DNS IPs.
    """
    LABEL = "Custom DNS servers"
    DESCRIPTION = "Connect to Proton VPN using your own domain name servers (DNS)."
    SETTING_NAME = "settings.custom_dns_enabled"

    def __init__(self, controller: Controller, gtk: Gtk = None):
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
        self.revealer = None

    @staticmethod
    def build(controller: Controller) -> "CustomDNSWidget":
        """Shortcut method to initialize widget."""
        widget = CustomDNSWidget(controller)
        widget.build_revealer()
        widget.show_all()
        return widget

    def build_revealer(self):
        """Builds the revealer"""
        self.revealer = self.gtk.Revealer()
        self.attach(self.revealer, 0, 2, 2, 1)
        revealer_container = self._build_revealer_container()
        self.revealer.add(revealer_container)
        self.revealer.set_reveal_child(self.get_setting())

    def _build_revealer_container(self) -> Gtk.Box:
        revealer_container = CustomDNSManager(self._controller)
        return revealer_container

    def _on_switch_button_toggle(self, _, new_value: bool, __):
        self.revealer.set_reveal_child(new_value)
        self.save_setting(new_value)
