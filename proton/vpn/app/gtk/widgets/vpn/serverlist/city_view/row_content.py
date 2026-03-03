"""
This module defines the row content displayed in the server list widget.


Copyright (c) 2026 Proton AG

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
from typing import List, Optional, Set, Tuple, Union
from gi.repository import GLib, GObject

from proton.vpn import logging
from proton.vpn.connection.enum import ConnectionStateEnum
from proton.vpn.session.servers import (
    City, Country, LogicalServer, ServerFeatureEnum, ServerList, TierEnum,
    SecureCoreGroup
)

from proton.vpn.app.gtk import Gtk
from proton.vpn.app.gtk.controller import Controller
from proton.vpn.app.gtk.utils.accessibility import add_accessibility, remove_accessibility
from proton.vpn.app.gtk.widgets.vpn.serverlist.icons import (
    P2PIcon, SecureCoreIcon, SmartRoutingIcon, TORIcon, UnderMaintenanceIcon
)

from proton.vpn.app.gtk.widgets.vpn.serverlist.server import ServerLoad
from proton.vpn.app.gtk.widgets.vpn.serverlist.city_view.hover_box import HoverBox

logger = logging.getLogger(__name__)


class RowContent(Gtk.Box):  # pylint: disable=too-many-instance-attributes
    """Row content in the server list."""
    # pylint: disable=too-many-arguments,too-many-statements

    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL)
        self.add_css_class("row-content")
        self._controller = None
        self._connected_signals: List[Tuple[int, Gtk.Widget]] = []

        # Properties
        self._server_group = None
        self._servers = None
        self._toggable = None
        self._user_tier = None
        self._connected_server_id = None
        self._expanded = None
        self._upgrade_required = None
        self._connection_state = None
        self._under_maintenance = None

        # UI widgets
        self._icon = None
        self._feature_icons = []
        self.set_spacing(10)
        self._label = Gtk.Label()
        self._label.set_halign(Gtk.Align.START)
        self.prepend(self._label)

        self._details = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self._details.set_halign(Gtk.Align.END)
        self._details.set_hexpand(True)
        self._details.set_spacing(10)

        # Add hidden label to widget tree for accessibility
        self._connect_button_label = Gtk.Label()  # Hidden label for accessibility
        self._connect_button_label.set_visible(False)
        self._details.append(self._connect_button_label)

        self.connect_button = self._build_connect_button()
        self.upgrade_required_link_button = self._build_upgrade_required_link_button()
        self._hover_box = HoverBox(
            on_show=lambda: self._feature_icons_box.set_visible(False),
            on_hide=lambda: self._feature_icons_box.set_visible(True),
            parent_for_hover=self,
        )
        self._details.append(self._hover_box)

        self._feature_icons_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self._feature_icons_box.set_spacing(10)
        self._feature_icons_box.set_halign(Gtk.Align.END)  # Right-align icons within the box
        self._details.append(self._feature_icons_box)

        self._server_load = ServerLoad(0)
        self._server_load.set_visible(False)
        self._details.append(self._server_load)

        self._details.set_visible(False)
        self.append(self._details)

        self.under_maintenance_icon = UnderMaintenanceIcon()
        self.under_maintenance_icon.add_css_class("under-maintenance-icon")
        self.under_maintenance_icon.set_halign(Gtk.Align.END)
        self.under_maintenance_icon.set_visible(False)
        self.append(self.under_maintenance_icon)

        self._collapsed_img = Gtk.Image.new_from_icon_name("pan-down-symbolic")
        self._expanded_img = Gtk.Image.new_from_icon_name("pan-up-symbolic")
        self.toggle_button = Gtk.Button()
        self.toggle_button.add_css_class("secondary")
        self.toggle_button.add_css_class("subtle-toggle")
        self.toggle_button.set_visible(False)
        self._details.append(self.toggle_button)

        self.connect("unrealize", self._on_unrealize)

    def display(
        self,
        controller: Controller,
        server_group: Union[Country, City, LogicalServer, SecureCoreGroup],
        user_tier: int,
        icon: Gtk.Image = None,
        connected_server_id: str = None,
        label: str = None
    ):
        """Displays the row content according to the specified parameters."""
        self.reset()
        self._controller = controller
        self._server_group = server_group
        self._icon = icon
        if self._icon:
            self.prepend(self._icon)
        self._toggable = isinstance(server_group, (Country, City, SecureCoreGroup))
        if isinstance(server_group, LogicalServer):
            self._server_load.set_visible(True)
            self._server_load.set_load(server_group.load)
            self._servers = [server_group]
        else:
            self._server_load.set_visible(False)
            self._servers = server_group.servers

        self._user_tier = user_tier
        self._connected_server_id = connected_server_id
        is_free_user = user_tier == TierEnum.FREE

        self._upgrade_required = is_free_user and not server_group.free
        self._connected_server_id = connected_server_id
        self._label.set_text(label or server_group.name)

        feature_icons = self._build_feature_icons()
        self._feature_icons = feature_icons
        for feature_icon in feature_icons:
            self._feature_icons_box.prepend(feature_icon)

        self._show_under_maintenance_icon_or_country_details()

        self.connection_state = ConnectionStateEnum.DISCONNECTED
        self._configure_connect_button()

        if self._toggable:
            self.toggle_button.set_visible(True)
            signal_id = self.toggle_button.connect("clicked", self._on_toggle_button_clicked)
            self._connected_signals.append((signal_id, self.toggle_button))
            self.expanded = False
        else:
            self.toggle_button.set_visible(False)

    def update_under_maintenance_status(self, under_maintenance: bool):
        """Shows or hides the under maintenance status for the country."""
        self._under_maintenance = under_maintenance
        self._show_under_maintenance_icon_or_country_details()

    def _show_under_maintenance_icon_or_country_details(self):
        if self.under_maintenance and not self.upgrade_required:
            # E.g. don't show that a paid country is under maintenance to free users
            # since they cannot connect to it anyway.
            self._show_under_maintenance_icon()
        else:
            self._show_country_details()

    def _show_under_maintenance_icon(self):
        self._details.set_visible(False)
        self.under_maintenance_icon.set_visible(True)
        help_text = f"{self.label} is under maintenance"
        self.under_maintenance_icon.set_help_text(help_text)
        self._label.set_property("sensitive", False)

    def _show_country_details(self):
        self.under_maintenance_icon.set_visible(False)
        if self._upgrade_required:
            self._hover_box.set_child(self.upgrade_required_link_button)
            self.connect_button.set_visible(False)
            self.upgrade_required_link_button.set_visible(True)
        else:
            self._hover_box.set_child(self.connect_button)
            self.connect_button.set_visible(True)
            self.upgrade_required_link_button.set_visible(False)
        self._details.set_visible(True)
        sensitive = not self._upgrade_required
        self._label.set_sensitive(sensitive)
        if self._icon:
            self._icon.set_sensitive(sensitive)
        for feature_icon in self._feature_icons:
            feature_icon.set_sensitive(sensitive)

    def _configure_connect_button(self):
        """Configures the connect button: accessibility, signals, and event handlers."""
        accessible_text = f"Connect to {self._server_group.name}"
        self.connect_button.set_tooltip_text(accessible_text)
        # Use hidden label with LABELLED_BY so Orca reads the accessible text
        self._connect_button_label.set_text(accessible_text)
        add_accessibility(
            self.connect_button,
            Gtk.AccessibleRelation.LABELLED_BY,
            self._connect_button_label
        )
        # Link feature icons to connect button for accessibility
        if self._feature_icons:
            add_accessibility(
                self.connect_button,
                Gtk.AccessibleRelation.DESCRIBED_BY,
                self._feature_icons
            )

        signal_id = self.connect_button.connect("clicked", self._on_connect_button_clicked)
        self._connected_signals.append((signal_id, self.connect_button))

    @property
    def under_maintenance(self) -> bool:
        """Indicates whether all the servers for this country are under maintenance or not."""
        return self._server_group.under_maintenance

    @property
    def upgrade_required(self):
        """Indicates whether the user needs to upgrade to have access to this country or not."""
        # pylint: disable=duplicate-code
        return self._upgrade_required

    def _build_upgrade_required_link_button(self) -> Gtk.LinkButton:
        upgrade_button = Gtk.LinkButton.new_with_label("Upgrade")
        upgrade_button.set_uri("https://account.protonvpn.com/")
        return upgrade_button

    def _build_connect_button(self) -> Gtk.Button:
        connect_button = Gtk.Button(label="Connect")
        connect_button.add_css_class("secondary")
        connect_button.add_css_class("connect-button")
        return connect_button

    def _build_feature_icons(self) -> List[Gtk.Image]:
        feature_icons = []
        if ServerFeatureEnum.SECURE_CORE in self._server_group.features:
            if isinstance(self._server_group, LogicalServer):
                feature_icons.append(SecureCoreIcon(
                    self._server_group.entry_country_name,
                    self._server_group.exit_country_name
                ))
            else:
                feature_icons.append(SecureCoreIcon())
        if self._server_group.smart_routing:
            feature_icons.append(SmartRoutingIcon())
        if ServerFeatureEnum.P2P in self._server_group.features:
            feature_icons.append(P2PIcon())
        if ServerFeatureEnum.TOR in self._server_group.features:
            feature_icons.append(TORIcon())
        return feature_icons

    @property
    def server_features(self) -> Set[ServerFeatureEnum]:
        """Returns the set of features supported by the servers in this country."""
        return self._server_group.features

    def get_feature_icons(self) -> List[Gtk.Image]:
        """Returns the list of feature icons currently displayed."""
        icons = []
        child = self._feature_icons_box.get_first_child()
        while child:
            icons.append(child)
            child = child.get_next_sibling()
        return icons

    @property
    def server_load(self) -> Optional[str]:
        """Returns the server load label text, or None if not visible."""
        if self._server_load.get_visible():
            return self._server_load.get_label()
        return None

    @GObject.Signal(name="toggle-children")
    def toggle_children(self):
        """Signal emitted when the user clicks the button to expand/collapse child rows."""

    @property
    def label(self):
        """Returns the name of the country this row content is for."""
        return self._label.get_text()

    @property
    def expanded(self):
        """Returns whether the row is expanded showing children rows if any."""
        return self._expanded

    @expanded.setter
    def expanded(self, value: bool):
        """Sets whether children rows should be shown or not."""
        self._expanded = value
        self.toggle_button.set_child(
            self._expanded_img if self.expanded else self._collapsed_img
        )
        tooltip_text = (
            f'{"Hide" if self.expanded else "Show"} all '
            f'{"cities" if isinstance(self._server_group, Country) else "servers"} '
            f'from {self.label}'
        )
        self.toggle_button.set_tooltip_text(tooltip_text)

    @property
    def available(self) -> bool:
        """Returns True if the country is available, meaning the user can
        connect to one of its servers. Otherwise, returns False."""
        return not self.upgrade_required and not self.under_maintenance

    @property
    def connection_state(self):
        """Returns the connection state of the server shown in this row."""
        return self._connection_state

    @connection_state.setter
    def connection_state(self, connection_state: ConnectionStateEnum):
        """Sets the connection state, modifying the row depending on the state."""
        # pylint: disable=duplicate-code
        self._connection_state = connection_state

    def _on_toggle_button_clicked(self, _toggle_button: Gtk.Button):
        self.expanded = not self.expanded
        self.emit("toggle-children")

    def _on_connect_button_clicked(self, _connect_button: Gtk.Button):
        fastest_server = ServerList.get_fastest_server(
            ServerList.get_available_servers(servers=self._servers, user_tier=self._user_tier)
        )
        future = self._controller.connect_to_server(fastest_server.name)
        future.add_done_callback(lambda f: GLib.idle_add(f.result))  # bubble up exceptions if any.

    def click_toggle_button(self):
        """Clicks the button to toggle the country servers.
        This method was made available for tests."""
        self.toggle_button.emit("clicked")

    def click_connect_button(self):
        """Clicks the button to connect to the country.
        This method was made available for tests."""
        self.connect_button.emit("clicked")

    def grab_focus(self):  # pylint: disable=arguments-differ
        """Focuses on the hover box child if available, otherwise the toggle."""
        hover_box_child = self._hover_box.get_child()
        if not self.under_maintenance and hover_box_child:
            # Focus on the connect button or the upgrade link
            hover_box_child.grab_focus()
        elif self.toggle_button:
            self.toggle_button.grab_focus()

    def _on_unrealize(self, _widget):
        """Called when widget is unrealized - performs cleanup."""
        self.reset()

    def reset(self):
        """Resets the state of this row content."""
        for signal_id, widget in self._connected_signals:
            widget.disconnect(signal_id)
        self._connected_signals.clear()
        self._hover_box.remove_child()
        self._remove_accessibility_relations()
        self._remove_icons()

    def _remove_accessibility_relations(self):
        """Clears all accessibility relations from the connect button."""
        remove_accessibility(self.connect_button, Gtk.AccessibleRelation.DESCRIBED_BY)
        remove_accessibility(self.connect_button, Gtk.AccessibleRelation.LABELLED_BY)

    def _remove_icons(self):
        """Removes all child widgets from parent widget, or from self if None."""
        if self._icon:
            self.remove(self._icon)
            self._icon = None

        for icon in self._feature_icons:
            self._feature_icons_box.remove(icon)

        self._feature_icons = []
