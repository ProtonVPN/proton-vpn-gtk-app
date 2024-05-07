"""
This module contains common objects that are used by different settings types.


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
from typing import Optional
from gi.repository import Gtk, Gdk


RECONNECT_MESSAGE = "Please establish a new VPN connection for "\
        "changes to take effect."


class BaseCategoryContainer(Gtk.Box):
    """Base container class that is used to group common settings.

    Mostly a helper class to remove the necessity of writing boilerplate
    styling code in each category container.
    """
    def __init__(self, category_name: str):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)

        self.get_style_context().add_class("setting-category")
        self.set_halign(Gtk.Align.FILL)
        self.set_spacing(15)

        self.pack_start(CategoryHeader(category_name), False, False, 0)


class CategoryHeader(Gtk.Label):
    """Header that is used to seperate between setting types, such as
    Features, Connection, etc."""
    def __init__(self, label: str):
        super().__init__(label=label)
        self.set_halign(Gtk.Align.START)
        style_context = self.get_style_context()
        style_context.add_class("heading")


class SettingRow(Gtk.Grid):
    """Contains the objects of a single item.

    The reason the `user_tier` is optional is mainly because some rows might
    be only available for free or paid plans, thus features that are free
    the `SettingRow` don't need a tier, but for paid features
    that can have another UI state (disabled state) we just need to pass the
    user tier for it to automatically display the propper UI.
    """
    def __init__(  # pylint: disable=too-many-arguments
        self, label: Gtk.Label,
        interactive_object: Gtk.Widget,
        description: Gtk.Label = None,
        user_tier: int = None,
    ):
        super().__init__()
        self.get_style_context().add_class("setting-item")
        self.set_halign(Gtk.Align.FILL)
        self.set_row_spacing(10)
        self.set_column_spacing(100)

        self._label = label
        self._interactive_object = interactive_object
        self._description = description

        self.build_ui(user_tier is not None and user_tier < 1)

    def build_ui(self, is_upgrade_required: bool):
        """Builds the UI depending if an upgrade is required or not."""
        if is_upgrade_required:
            self._label.enabled = False
            self._interactive_object = UpgradePlusTag()

        self.attach(self._label, 0, 0, 1, 1)

        # Style interactive_object so it's always aligned
        self._interactive_object.set_hexpand(True)
        self._interactive_object.set_halign(Gtk.Align.END)

        self.attach(self._interactive_object, 1, 0, 1, 1)

        if self._description:
            self.attach(self._description, 0, 1, 2, 1)

    @property
    def name(self) -> Gtk.Label:
        """Returns Gtk object that contains the name of the setting"""
        return self._label

    @property
    def interactive_object(self) -> Gtk.Widget:
        """Returns Gtk object that contains the interactive object that
        the user can interact with."""
        return self._interactive_object

    @property
    def description(self) -> Optional[Gtk.Label]:
        """Returns Gtk object (or None) that contains the description of the setting"""
        return self._description

    @property
    def enabled(self) -> bool:
        """Returns if the widget is enabled."""
        return self.get_property("sensitive")

    @enabled.setter
    def enabled(self, newvalue: bool):
        """Set if the widget should be enabled."""
        self.set_property("sensitive", newvalue)

    @property
    def overridden_by_upgrade_tag(self) -> bool:
        """Returns if the the upgrade tag has overriden original interactive
        object."""
        return isinstance(self._interactive_object, UpgradePlusTag)

    def set_tooltip(self, tooltip_text: str):
        """Set a tooltip to this row."""
        self.set_has_tooltip(True)
        self.set_tooltip_text(tooltip_text)


class UpgradePlusTag(Gtk.Button):
    """ Using normal button instead of LinkButton mainly
    because of styling. LinkButtons usually have very ugly UI,
    and all they do is emit `::activate-link` which
    just calls `Gtk.show_uri_on_window`.

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
    def __init__(self, label: str, bold: bool = False):
        if bold:
            label = f"<b>{label}</b>"

        super().__init__(label=label)
        self.set_halign(Gtk.Align.START)
        self.set_hexpand(True)
        self.set_use_markup(True)

    @property
    def enabled(self) -> bool:
        """Returns if the label is enabled."""
        return self.get_property("sensitive")

    @enabled.setter
    def enabled(self, newvalue: bool):
        """Sets if the label should be enabled."""
        self.set_property("sensitive", newvalue)


class SettingDescription(Gtk.Label):
    """Label used to desribe a setting."""
    def __init__(self, label: str):
        super().__init__(label=label)
        self.get_style_context().add_class("dim-label")
        self.set_line_wrap(True)
        self.set_max_width_chars(1)
        self.set_property("xalign", 0)
        self.set_hexpand(True)
        self.set_use_markup(True)
