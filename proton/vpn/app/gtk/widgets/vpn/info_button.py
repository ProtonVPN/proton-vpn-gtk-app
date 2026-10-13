"""
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

A borderless button with an info icon that opens a popover.
"""
from gi.repository import Gdk

from proton.vpn.app.gtk import Gtk
from proton.vpn.app.gtk.assets import icons


def info_menu_button(popover: Gtk.Popover, label: str) -> Gtk.MenuButton:
    """A borderless button showing an info icon that opens `popover`.

    :param label: names the button for screen readers, since its only child
        is an icon.
    """
    button = Gtk.MenuButton()
    button.add_css_class("ghost")
    button.set_has_frame(False)
    button.update_property([Gtk.AccessibleProperty.LABEL], [label])
    button.set_popover(popover)
    button.set_direction(Gtk.ArrowType.DOWN)
    button.set_always_show_arrow(False)
    button.set_cursor(Gdk.Cursor.new_from_name("pointer", None))
    button.set_child(Gtk.Image.new_from_gicon(icons.file_icon("info-symbolic.svg")))
    return button
