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


Tests that the app's dark colour scheme remains in effect when the desktop
changes the theme, as it does when high contrast turns on or off.
"""
import pytest

from proton.vpn.app.gtk import Gtk
from proton.vpn.app.gtk.app import prefer_dark_colour_scheme
from proton.vpn.app.gtk.assets.style import MIN_GTK_INTERFACE_SETTINGS
from tests.unit.testing_utils import process_gtk_events

GTK_VERSION = (Gtk.get_major_version(), Gtk.get_minor_version(), Gtk.get_micro_version())
pytestmark = pytest.mark.skipif(
    GTK_VERSION < MIN_GTK_INTERFACE_SETTINGS, reason="needs GTK 4.20 or later"
)


@pytest.fixture
def label():
    """A label in a shown window, styled by GTK's theme only, with the dark
    colour scheme preferred."""
    settings = Gtk.Settings.get_default()
    handler_id = prefer_dark_colour_scheme()
    widget = Gtk.Label(label="text")
    window = Gtk.Window(child=widget)
    window.present()
    yield widget
    window.destroy()
    settings.disconnect(handler_id)
    for setting in ("gtk-theme-name", "gtk-interface-contrast", "gtk-interface-color-scheme"):
        settings.reset_property(setting)


def _has_light_text(widget: Gtk.Label) -> bool:
    """Whether the label's text is light, as in the dark colour scheme."""
    process_gtk_events()
    color = widget.get_color()
    return (color.red + color.green + color.blue) / 3 > 0.5


# pylint: disable-next=redefined-outer-name
def test_dark_colour_scheme_remains_after_the_theme_changes(label):
    Gtk.Settings.get_default().props.gtk_theme_name = "Adwaita"

    assert _has_light_text(label)


# pylint: disable-next=redefined-outer-name
def test_dark_colour_scheme_remains_in_gnome_high_contrast(label):
    settings = Gtk.Settings.get_default()

    settings.props.gtk_interface_contrast = Gtk.InterfaceContrast.MORE
    settings.props.gtk_theme_name = "HighContrast"

    assert _has_light_text(label)
