"""
Settings window module.


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
from __future__ import annotations

from gi.repository import Gtk, Gdk
from proton.vpn.app.gtk.controller import Controller
from proton.vpn.app.gtk.widgets.main.notification_bar import NotificationBar
from proton.vpn.core_api.settings import NetShield


RECONNECT_MESSAGE = "Please establish a new VPN connection for "\
        "changes to take effect."


class SettingsWindow(Gtk.Window):
    """Main settings window."""
    def __init__(
        self,
        controller: Controller,
        notification_bar: NotificationBar = None,
        feature_settings: FeatureSettings = None,
        connection_settings: ConnectionSettings = None
    ):
        super().__init__()
        self.set_title("Settings")
        self.set_default_size(600, 500)
        self.set_modal(True)

        self._controller = controller
        self._notification_bar = notification_bar or NotificationBar()

        self._feature_settings = feature_settings or FeatureSettings(
            self._controller, self._notification_bar
        )
        self._connection_settings = connection_settings or ConnectionSettings(
            self._controller, self._notification_bar
        )

        self._create_elastic_window()

        self.connect("realize", self._build_ui)

    def _build_ui(self, *_):
        self._connection_settings.build_ui()
        self._feature_settings.build_ui()
        self.show_all()

    def _create_elastic_window(self):
        """This allows for the content to be always centered and expand or contract
        based on window size.

        The reason we use two containers is mainly due to the notification bar, as this
        way the notification will span across the entire window while only the
        settings will be centered.
        """
        self.main_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.content_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

        self.content_container.pack_start(self._feature_settings, False, False, 0)
        self.content_container.pack_start(self._connection_settings, False, False, 0)

        viewport = Gtk.Viewport()
        viewport.get_style_context().add_class("viewport-frame")
        viewport.add(self.content_container)

        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_property("window-placement", False)
        scrolled_window.set_propagate_natural_height(True)
        scrolled_window.set_min_content_height(300)
        scrolled_window.set_min_content_width(400)
        scrolled_window.add(viewport)

        self.main_container.pack_start(self._notification_bar, False, False, 0)
        self.main_container.pack_start(scrolled_window, False, False, 0)

        self.add(self.main_container)


class FeatureSettings(Gtk.Box):
    """Settings related to connection are all grouped under this class."""
    CATEGORY_NAME = "Features"
    NETSHIELD_LABEL = "NetShield"
    NETSHIELD_DESCRIPTION = "Protect yourself from ads, malware, and trackers "\
        "on websites and apps."

    def __init__(self, controller: Controller, notification_bar: NotificationBar):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self._controller = controller
        self._notification_bar = notification_bar

        self.netshield_combobox = None
        self.netshield_row = None

        self.set_halign(Gtk.Align.FILL)
        self.set_spacing(15)

        self.get_style_context().add_class("setting-category")

    def build_ui(self):
        """Builds the UI, invoking all necessary methods that are
        under this category."""
        self.pack_start(CategoryHeader(self.CATEGORY_NAME), False, False, 0)
        self.build_netshield()

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

        netshield_options = [
            (str(NetShield.NO_BLOCK.value), "Off"),
            (str(NetShield.BLOCK_MALICIOUS_URL.value), "Block Malware"),
            (str(NetShield.BLOCK_ADS_AND_TRACKING.value), "Block ads, trackers and malware"),
        ]
        self.netshield_combobox = Gtk.ComboBoxText()
        self.netshield_combobox.set_hexpand(True)
        self.netshield_combobox.set_halign(Gtk.Align.END)

        for netshield_option in netshield_options:
            id_, ui_friendly_text = netshield_option
            self.netshield_combobox.append(id_, ui_friendly_text)

        self.netshield_row = SettingRow(
            SettingName(self.NETSHIELD_LABEL),
            self.netshield_combobox,
            SettingDescription(self.NETSHIELD_DESCRIPTION),
            self._controller.user_tier
        )

        self.pack_start(self.netshield_row, False, False, 0)

        if not self._controller.vpn_data_refresher.client_config.feature_flags.netshield:
            self.netshield_row.set_property("sensitive", False)
            self.netshield = NetShield.NO_BLOCK.value

        self.netshield_combobox.set_entry_text_column(1)
        self.netshield_combobox.set_active_id(self.netshield)
        self.netshield_combobox.connect("changed", on_combobox_changed)


class ConnectionSettings(Gtk.Box):
    """Settings related to connection are all grouped under this class."""
    CATEGORY_NAME = "Connection"
    PROTOCOL_LABEL = "Protocol"
    VPN_ACCELERATOR_LABEL = "VPN Accelerator"
    VPN_ACCELERATOR_DESCRIPTION = "Increase your connection speed by up to 400% "\
        "with performance enhancing technologies."

    def __init__(self, controller: Controller, notification_bar: NotificationBar):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self._controller = controller
        self._notification_bar = notification_bar

        self.set_halign(Gtk.Align.FILL)
        self.set_spacing(15)

        self.vpn_accelerator_switch = None
        self.protocol_combobox = None
        self.vpn_accelerator_row = None

        self.get_style_context().add_class("setting-category")

    def build_ui(self):
        """Builds the UI, invoking all necessary methods that are
        under this category."""
        self.pack_start(CategoryHeader(self.CATEGORY_NAME), False, False, 0)
        self.build_protocol()
        self.build_vpn_accelerator()

    @property
    def protocol(self) -> str:
        """Shortcut property that returns the current `protocol` setting"""
        return self._controller.get_settings().protocol

    @protocol.setter
    def protocol(self, newvalue: str):
        """Shortcut property that sets the new `protocol` setting and
        stores to disk."""
        self._controller.get_settings().protocol = newvalue
        self._controller.save_settings()

    @property
    def vpn_accelerator(self) -> bool:
        """Shortcut property that returns the current `vpn_accelerator` setting"""
        return self._controller.get_settings().features.vpn_accelerator

    @vpn_accelerator.setter
    def vpn_accelerator(self, newvalue: bool):
        """Shortcut property that sets the new `vpn_accelerator` setting and
        stores to disk."""
        self._controller.get_settings().features.vpn_accelerator = newvalue
        self._controller.save_settings()

    def build_protocol(self):
        """Builds and adds the `protocol` setting to the widget."""
        def on_combobox_changed(combobox):
            model = combobox.get_model()
            treeiter = combobox.get_active_iter()
            protocol = model[treeiter][0]
            self.protocol = protocol
            if self._controller.is_connection_active:
                self._notification_bar.show_info_message(
                    f"{RECONNECT_MESSAGE}"
                )

        available_protocols = self._controller.get_available_protocols()
        self.protocol_combobox = Gtk.ComboBoxText()
        self.protocol_combobox.set_hexpand(True)
        self.protocol_combobox.set_halign(Gtk.Align.END)

        for protocol in available_protocols:
            self.protocol_combobox.append(protocol, protocol)

        self.protocol_combobox.set_entry_text_column(1)
        self.protocol_combobox.set_active_id(self.protocol)
        self.protocol_combobox.connect("changed", on_combobox_changed)

        self.pack_start(
            SettingRow(
                SettingName(self.PROTOCOL_LABEL),
                self.protocol_combobox
            ), False, False, 0
        )

    def build_vpn_accelerator(self):
        """Builds and adds the `vpn_accelerator` setting to the widget."""
        def on_switch_state(_, new_value: bool):
            self.vpn_accelerator = new_value
            if self._controller.is_connection_active:
                self._notification_bar.show_info_message(
                    f"{RECONNECT_MESSAGE}"
                )

        self.vpn_accelerator_switch = Gtk.Switch()
        self.vpn_accelerator_switch.set_halign(Gtk.Align.END)
        self.vpn_accelerator_switch.set_hexpand(True)

        self.vpn_accelerator_row = SettingRow(
            SettingName(self.VPN_ACCELERATOR_LABEL),
            self.vpn_accelerator_switch,
            SettingDescription(self.VPN_ACCELERATOR_DESCRIPTION)
        )
        self.pack_start(self.vpn_accelerator_row, False, False, 0)

        if not self._controller.vpn_data_refresher.client_config.feature_flags.vpn_accelerator:
            self.vpn_accelerator_row.set_property("sensitive", False)
            self.vpn_accelerator = False

        self.vpn_accelerator_switch.set_state(self.vpn_accelerator)
        self.vpn_accelerator_switch.connect("state-set", on_switch_state)


class CategoryHeader(Gtk.Label):
    """Header that is used to seperate between setting types, such as
    Features, Connection, etc."""
    def __init__(self, label: str):
        super().__init__(label=label)
        self.set_halign(Gtk.Align.START)
        style_context = self.get_style_context()
        style_context.add_class("heading")


class SettingRow(Gtk.Grid):
    """Contains the objects of a single item."""
    def __init__(
        self, label: Gtk.Label,
        interactive_object: Gtk.Widget,
        description: Gtk.Label = None, user_tier: int = None
    ):
        super().__init__()
        self.get_style_context().add_class("setting-item")
        self.set_halign(Gtk.Align.FILL)
        self.set_row_spacing(10)
        self.set_column_spacing(100)

        self._user_tier = user_tier

        self._label = label
        self._interactive_object = interactive_object
        self._description = description

        self.build_ui(self._user_tier is not None and self._user_tier < 1)

    def build_ui(self, is_upgrade_required: bool):
        """Builds the UI depending if an upgrade is required or not."""
        if is_upgrade_required:
            self._label.disabled = True
            self._interactive_object = UpgradePlusTag()

        self.attach(self._label, 0, 0, 1, 1)
        self.attach(self._interactive_object, 1, 0, 1, 1)

        if self._description:
            self.attach(self._description, 0, 1, 2, 1)

    @property
    def overriden_by_upgrade_tag(self) -> bool:
        """Returns if the the upgrade tag has overriden original interactive
        object."""
        return isinstance(self._interactive_object, UpgradePlusTag)


class UpgradePlusTag(Gtk.Button):
    """ Using normal button instead of LinkButton mainly
    because of styling. LinkButtons usually have very ugly UI,
    and all they do is emit `::activate-link which`
    just calls `Gtk.show_uri_on_window`

    Source: https://lazka.github.io/pgi-docs/Gtk-3.0/classes/LinkButton.html
    """
    LABEL = "VPN Plus"
    URL = "https://protonvpn.com/pricing"

    def __init__(self):
        super().__init__(label=self.LABEL)
        self.get_style_context().add_class("upgrade-tag")
        self.get_style_context().add_class("heading")
        self.connect("clicked", self._on_button_clicked)

    def _on_button_clicked(self, _):
        Gtk.show_uri_on_window(
            None,
            self.URL,
            Gdk.CURRENT_TIME
        )


class SettingName(Gtk.Label):
    """Label used to identify a setting."""
    def __init__(self, label: str):
        super().__init__(label=label)
        self.set_halign(Gtk.Align.START)
        self.set_hexpand(True)

    @property
    def disabled(self) -> bool:
        """Returns if the label is disabled or not."""
        return not self.get_property("sensitive")

    @disabled.setter
    def disabled(self, newvalue: bool):
        """Sets of the label should be disabled or not."""
        self.set_property("sensitive", not newvalue)


class SettingDescription(Gtk.Label):
    """Label used to desribe a setting."""
    def __init__(self, label: str):
        super().__init__(label=label)
        self.get_style_context().add_class("dim-label")
        self.set_line_wrap(True)
        self.set_max_width_chars(1)
        self.set_property("xalign", 0)
        self.set_hexpand(True)
