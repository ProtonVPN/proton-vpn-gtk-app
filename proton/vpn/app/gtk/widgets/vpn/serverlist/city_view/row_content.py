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

from proton.vpn.session.servers import ServerFeatureEnum

from proton.vpn.app.gtk.widgets.vpn.serverlist.city_view.row_view_model import RowViewModel

from proton.vpn.app.gtk import Gtk
from proton.vpn.app.gtk.utils.accessibility import add_accessibility, remove_accessibility
from proton.vpn.app.gtk.utils.safe_signal_connect import safe_signal_connect
from proton.vpn.app.gtk.widgets.vpn.serverlist.icons import (
    LocationIcon, P2PIcon, SecureCoreIcon, SmartRoutingIcon, TORIcon, UnderMaintenanceIcon
)

from proton.vpn.app.gtk.widgets.vpn.serverlist.city_view.server_load import ServerLoad
from proton.vpn.app.gtk.widgets.vpn.serverlist.city_view.hover_stack import HoverStack

logger = logging.getLogger(__name__)

UPGRADE_URL = "https://account.protonvpn.com/"


class RowContent(Gtk.Box):  # pylint: disable=too-many-instance-attributes
    """Row content in the server list."""
    # pylint: disable=too-many-arguments,too-many-statements

    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL)
        self.add_css_class("row-content")
        self._connected_signals: List[Tuple[int, Gtk.Widget]] = []

        # Properties
        self._row_data: Optional[RowViewModel] = None
        self._expanded: Optional[bool] = None
        self._icon_leave: Optional[Gtk.Widget] = None
        self._icon_hover: Optional[Gtk.Widget] = None

        # UI widgets
        self._feature_icons: List[Gtk.Image] = []
        self.set_spacing(10)

        # _leave_box contains widget shown when the row doesn't have focus nor it's hovered
        self._leave_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self._leave_box.add_css_class("row-leave-box")

        self._label = Gtk.Label()
        self._label.set_halign(Gtk.Align.START)
        self._label.set_hexpand(True)

        self._feature_icons_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self._feature_icons_box.set_spacing(10)
        self._feature_icons_box.set_halign(Gtk.Align.END)

        self._server_load = ServerLoad(0)
        self._server_load.set_visible(False)

        self._leave_box.append(self._label)
        self._leave_box.append(self._feature_icons_box)
        self._leave_box.append(self._server_load)

        # --- Hover child: full-width flat button ---
        # Mirrors _label from the leave child: shows the row name on the left.
        self._hover_name_label = Gtk.Label()
        self._hover_name_label.set_halign(Gtk.Align.START)
        self._hover_name_label.set_hexpand(True)

        # Shows the action text ("Connect" or "Upgrade") on the right.
        self._hover_action_label = Gtk.Label()
        self._hover_action_label.set_halign(Gtk.Align.END)
        self._hover_action_label.add_css_class("connect-action-label")

        self._hover_button_content = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL, spacing=10
        )
        self._hover_button_content.add_css_class("row-hover-box")
        self._hover_button_content.append(self._hover_name_label)
        self._hover_button_content.append(self._hover_action_label)

        self.action_button = Gtk.Button()
        self.action_button.add_css_class("flat")
        self.action_button.add_css_class("connect-button")
        self.action_button.set_hexpand(True)
        self.action_button.set_child(self._hover_button_content)

        # Hidden label for accessibility
        self._accessibility_label = Gtk.Label()
        self._accessibility_label.set_visible(False)

        self._hover_stack = HoverStack()
        self._hover_stack.add_css_class("row-hover-stack")
        self._hover_stack.set_hexpand(True)
        self.append(self._hover_stack)
        self.append(self._accessibility_label)

        # --- Under maintenance icon ---
        self.under_maintenance_icon = UnderMaintenanceIcon()
        self.under_maintenance_icon.add_css_class("under-maintenance-icon")
        self.under_maintenance_icon.set_halign(Gtk.Align.END)
        self.under_maintenance_icon.set_hexpand(True)
        self.under_maintenance_icon.set_visible(False)
        self.append(self.under_maintenance_icon)

        # --- Toggle button (outside stack, always at the end) ---
        self._collapsed_img = Gtk.Image.new_from_icon_name("pan-down-symbolic")
        self._expanded_img = Gtk.Image.new_from_icon_name("pan-up-symbolic")
        self.toggle_button = Gtk.Button()
        self.toggle_button.add_css_class("toggle-button")
        self.toggle_button.add_css_class("flat")
        self._set_toggle_button_visible(False)
        self.append(self.toggle_button)

        safe_signal_connect(self, "unrealize", self._on_unrealize)

    def display(self, row_data: RowViewModel):
        """Displays the row content according to the specified parameters."""
        self.reset()
        self._row_data = row_data

        # Create two independent icon instances: one for leave, one for hover.
        if row_data.icon_factory is not None:
            self._icon_leave = row_data.icon_factory()
            self._icon_hover = row_data.icon_factory()
        else:
            self._icon_leave = Gtk.Image()
            self._icon_leave.set_size_request(LocationIcon.SIZE, LocationIcon.SIZE)
            self._icon_hover = Gtk.Image()
            self._icon_hover.set_size_request(LocationIcon.SIZE, LocationIcon.SIZE)

        self._leave_box.prepend(self._icon_leave)
        self._hover_button_content.prepend(self._icon_hover)
        self._hover_name_label.set_text(row_data.name)

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
        self._hover_stack.set_leave_child(self._leave_box)

        if self._row_data.under_maintenance:
            self._show_under_maintenance_icon()
        else:
            self._show_hover_stack()
            self._configure_connect_button(row_data.connect_button_tooltip)

        if row_data.toggable:
            self._set_toggle_button_visible(True)
            signal_id = safe_signal_connect(
                self.toggle_button,
                "clicked",
                self._on_toggle_button_clicked
            )
            self._connected_signals.append((signal_id, self.toggle_button))
            self.expanded = False
        else:
            self._set_toggle_button_visible(False)

    def _show_under_maintenance_icon(self):
        self.under_maintenance_icon.set_visible(True)
        help_text = f"{self.label} is under maintenance"
        self.under_maintenance_icon.set_help_text(help_text)
        self.add_css_class("dimmed")

    def _show_hover_stack(self):
        self.under_maintenance_icon.set_visible(False)
        self._hover_stack.set_visible(True)
        if self._row_data.upgrade_required:
            self._hover_action_label.set_text("Upgrade")
            signal_id = safe_signal_connect(
                self.action_button,
                "clicked",
                self._on_upgrade_button_clicked
            )
            self.add_css_class("dimmed")
        else:
            self._hover_action_label.set_text("Connect")
            signal_id = safe_signal_connect(
                self.action_button,
                "clicked",
                self._on_connect_button_clicked
            )
        self._connected_signals.append((signal_id, self.action_button))
        self._hover_stack.set_hover_child(self.action_button)

    def _configure_connect_button(self, tooltip: str):
        """Configures the connect button: accessibility, signals, and event handlers."""
        self.action_button.set_tooltip_text(tooltip)
        self._accessibility_label.set_text(tooltip)
        add_accessibility(
            self.action_button,
            Gtk.AccessibleRelation.LABELLED_BY,
            self._accessibility_label
        )
        if self._feature_icons:
            add_accessibility(
                self.action_button,
                Gtk.AccessibleRelation.DESCRIBED_BY,
                self._feature_icons
            )

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
    def details_visible(self) -> bool:
        """Returns whether the row has interactive details (connect/upgrade button)."""
        return self._hover_stack.get_hover_child() is not None

    @property
    def action_text(self) -> str:
        """Returns the text of the connect/upgrade action label."""
        return self._hover_action_label.get_text()

    @property
    def label_sensitive(self) -> bool:
        """Returns whether the row is not dimmed."""
        return not self.has_css_class("dimmed")

    @property
    def icon(self) -> Optional[Gtk.Widget]:
        """Returns the leave-child icon widget for this row, or None if not set."""
        return self._icon_leave

    @property
    def connect_button_tooltip(self) -> Optional[str]:
        """Returns the connect button tooltip text."""
        return self.action_button.get_tooltip_text()

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

    def _set_toggle_button_visible(self, visible: bool):
        """Show or hide the toggle button while keeping it in the layout.

        set_opacity(0) keeps the space reserved to avoid layout shifts,
        but we also set_sensitive(False) so it is removed from the tab
        order and screen reader tree when invisible.
        """
        self.toggle_button.set_opacity(1 if visible else 0)
        self.toggle_button.set_sensitive(visible)

    def _on_toggle_button_clicked(self, _toggle_button: Gtk.Button):
        self.expanded = not self.expanded
        self.emit("toggle-children")

    def _on_connect_button_clicked(self, _connect_button: Gtk.Button):
        self._row_data.on_connect()
        self._hover_stack.show_leave_child()

    def _on_upgrade_button_clicked(self, _connect_button: Gtk.Button):
        Gtk.show_uri(self.get_root(), UPGRADE_URL, 0)
        self._hover_stack.show_leave_child()

    def click_toggle_button(self):
        """Clicks the button to toggle the country servers.
        This method was made available for tests."""
        self.toggle_button.emit("clicked")

    def click_action_button(self):
        """Clicks the button to connect to the country.
        This method was made available for tests."""
        self.action_button.emit("clicked")

    def get_feature_icons(self) -> List[Gtk.Image]:
        """Returns the list of feature icons currently displayed."""
        icons = []
        child = self._feature_icons_box.get_first_child()
        while child:
            icons.append(child)
            child = child.get_next_sibling()
        return icons

    @property
    def server_features(self) -> Set[ServerFeatureEnum]:
        """Returns the set of features supported by the servers in this country."""
        return self._row_data.features

    def grab_focus(self):  # pylint: disable=arguments-differ
        """Focuses on the connect button if available, otherwise the toggle."""
        if not self._row_data.under_maintenance:
            self._hover_stack.show_hover_child()
            self.action_button.grab_focus()
        elif self.toggle_button.get_sensitive():
            self.toggle_button.grab_focus()

    def _on_unrealize(self, _widget):
        """Called when widget is unrealized - performs cleanup."""
        self.reset()

    def reset(self):
        """Resets the state of this row content."""
        self.remove_css_class("dimmed")
        for signal_id, widget in self._connected_signals:
            widget.disconnect(signal_id)
        self._connected_signals.clear()
        self._hover_stack.reset()
        self._remove_accessibility_relations()
        self._remove_icons()
        self._row_data = None

    def _remove_accessibility_relations(self):
        """Clears all accessibility relations from the connect button."""
        remove_accessibility(self.action_button, Gtk.AccessibleRelation.DESCRIBED_BY)
        remove_accessibility(self.action_button, Gtk.AccessibleRelation.LABELLED_BY)

    def _remove_icons(self):
        """Removes dynamically added icon widgets and feature icons."""
        if self._icon_leave and self._icon_leave.get_parent() == self._leave_box:
            self._leave_box.remove(self._icon_leave)
            self._icon_leave = None

        if self._icon_hover and self._icon_hover.get_parent() == self._hover_button_content:
            self._hover_button_content.remove(self._icon_hover)
            self._icon_hover = None

        for icon in self._feature_icons:
            self._feature_icons_box.remove(icon)
        self._feature_icons = []
