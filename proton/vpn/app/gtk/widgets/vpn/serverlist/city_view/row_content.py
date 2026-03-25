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
from typing import List, Optional, Set, Tuple
from gi.repository import GObject

from proton.vpn import logging
from proton.vpn.connection.enum import ConnectionStateEnum
from proton.vpn.session.servers import ServerFeatureEnum

from proton.vpn.app.gtk.widgets.vpn.serverlist.city_view.row_view_model import RowViewModel

from proton.vpn.app.gtk import Gtk
from proton.vpn.app.gtk.utils.accessibility import add_accessibility, remove_accessibility
from proton.vpn.app.gtk.widgets.vpn.serverlist.icons import (
    P2PIcon, SecureCoreIcon, SmartRoutingIcon, TORIcon, UnderMaintenanceIcon
)

from proton.vpn.app.gtk.widgets.vpn.serverlist.server import ServerLoad
from proton.vpn.app.gtk.widgets.vpn.serverlist.city_view.hover_stack import HoverStack

logger = logging.getLogger(__name__)


class RowContent(Gtk.Box):  # pylint: disable=too-many-instance-attributes
    """Row content in the server list."""
    # pylint: disable=too-many-arguments,too-many-statements

    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL)
        self.add_css_class("row-content")
        self._connected_signals: List[Tuple[int, Gtk.Widget]] = []

        # Properties
        self._row_data = None
        self._expanded = None
        self._connection_state = None

        # UI widgets
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

        self._feature_icons_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self._feature_icons_box.set_spacing(10)
        self._feature_icons_box.set_halign(Gtk.Align.END)
        self._hover_stack = HoverStack(parent_for_hover=self)
        self._details.append(self._hover_stack)

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

    def display(self, row_data: RowViewModel):
        """Displays the row content according to the specified parameters."""
        self.reset()
        self._row_data = row_data
        if row_data.icon:
            self.prepend(row_data.icon)
        if row_data.load is not None:
            self._server_load.set_visible(True)
            self._server_load.set_load(row_data.load)
        else:
            self._server_load.set_visible(False)

        self._label.set_text(row_data.name)

        feature_icons = self._build_feature_icons(row_data)
        self._feature_icons = feature_icons
        for feature_icon in feature_icons:
            self._feature_icons_box.prepend(feature_icon)
        self._hover_stack.set_leave_child(self._feature_icons_box)

        if self._row_data.under_maintenance:
            self._show_under_maintenance_icon()
        else:
            self._show_country_details()

        self.connection_state = ConnectionStateEnum.DISCONNECTED
        self._configure_connect_button(row_data.connect_button_tooltip)

        if row_data.toggable:
            self.toggle_button.set_visible(True)
            signal_id = self.toggle_button.connect("clicked", self._on_toggle_button_clicked)
            self._connected_signals.append((signal_id, self.toggle_button))
            self.expanded = False
        else:
            self.toggle_button.set_visible(False)

    def _show_under_maintenance_icon(self):
        self._details.set_visible(False)
        self.under_maintenance_icon.set_visible(True)
        help_text = f"{self.label} is under maintenance"
        self.under_maintenance_icon.set_help_text(help_text)
        self._label.set_property("sensitive", False)

    def _show_country_details(self):
        self.under_maintenance_icon.set_visible(False)
        if self._row_data.upgrade_required:
            self._hover_stack.set_hover_child(self.upgrade_required_link_button)
            self.connect_button.set_visible(False)
            self.upgrade_required_link_button.set_visible(True)
        else:
            self._hover_stack.set_hover_child(self.connect_button)
            self.connect_button.set_visible(True)
            self.upgrade_required_link_button.set_visible(False)
        self._details.set_visible(True)
        sensitive = not self._row_data.upgrade_required
        self._label.set_sensitive(sensitive)
        if self._row_data.icon:
            self._row_data.icon.set_sensitive(sensitive)
        for feature_icon in self._feature_icons:
            feature_icon.set_sensitive(sensitive)

    def _configure_connect_button(self, tooltip: str):
        """Configures the connect button: accessibility, signals, and event handlers."""
        self.connect_button.set_tooltip_text(tooltip)
        # Use hidden label with LABELLED_BY so Orca reads the accessible text
        self._connect_button_label.set_text(tooltip)
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

    def _build_upgrade_required_link_button(self) -> Gtk.LinkButton:
        upgrade_button = Gtk.LinkButton.new_with_label("Upgrade")
        upgrade_button.set_uri("https://account.protonvpn.com/")
        return upgrade_button

    def _build_connect_button(self) -> Gtk.Button:
        connect_button = Gtk.Button(label="Connect")
        connect_button.add_css_class("secondary")
        connect_button.add_css_class("connect-button")
        return connect_button

    def _build_feature_icons(self, row_data: RowViewModel) -> List[Gtk.Image]:
        feature_icons: List[Gtk.Image] = []
        if ServerFeatureEnum.SECURE_CORE in row_data.features:
            if row_data.secure_core_countries:
                entry, exit_ = row_data.secure_core_countries
                feature_icons.append(SecureCoreIcon(entry, exit_))
            else:
                feature_icons.append(SecureCoreIcon())
        if row_data.smart_routing:
            feature_icons.append(SmartRoutingIcon())
        if ServerFeatureEnum.P2P in row_data.features:
            feature_icons.append(P2PIcon())
        if ServerFeatureEnum.TOR in row_data.features:
            feature_icons.append(TORIcon())
        return feature_icons

    @property
    def server_features(self) -> Set[ServerFeatureEnum]:
        """Returns the set of features supported by the servers in this country."""
        return self._row_data.features

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
            self._row_data.toggle_button_tooltips[1]
            if self.expanded else self._row_data.toggle_button_tooltips[0]
        )
        self.toggle_button.set_tooltip_text(tooltip_text)

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
        self._row_data.on_connect()

    def click_toggle_button(self):
        """Clicks the button to toggle the country servers.
        This method was made available for tests."""
        self.toggle_button.emit("clicked")

    def click_connect_button(self):
        """Clicks the button to connect to the country.
        This method was made available for tests."""
        self.connect_button.emit("clicked")

    def grab_focus(self):  # pylint: disable=arguments-differ
        """Focuses on the connect button if available, otherwise the toggle."""
        connect_child = self._hover_stack.get_hover_child()
        if not self._row_data.under_maintenance and connect_child:
            self._hover_stack.show_hover_child()
            connect_child.grab_focus()
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
        self._hover_stack.reset()
        self._remove_accessibility_relations()
        self._remove_icons()
        self._row_data = None

    def _remove_accessibility_relations(self):
        """Clears all accessibility relations from the connect button."""
        remove_accessibility(self.connect_button, Gtk.AccessibleRelation.DESCRIBED_BY)
        remove_accessibility(self.connect_button, Gtk.AccessibleRelation.LABELLED_BY)

    def _remove_icons(self):
        """Removes all child widgets from parent widget, or from self if None."""
        if self._row_data and self._row_data.icon and self._row_data.icon.get_parent() == self:
            self.remove(self._row_data.icon)

        for icon in self._feature_icons:
            self._feature_icons_box.remove(icon)

        self._feature_icons = []
