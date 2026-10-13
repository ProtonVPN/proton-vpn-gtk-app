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


Demo factories for the app bar (the windows' title bar).
"""
from unittest.mock import MagicMock

from proton.vpn.app.gtk import Gtk
from proton.vpn.app.gtk.demo.mocks import mock_controller, mock_main_window
from proton.vpn.app.gtk.demo.registry import register_demo
from proton.vpn.app.gtk.demo.sizing import NATURAL
from proton.vpn.app.gtk.utils.window import PROTON_APP_CSS_CLASS
from proton.vpn.app.gtk.widgets.headerbar.headerbar import HeaderBar
from proton.vpn.app.gtk.widgets.main.main_window import MainWindow


def _in_app_window(header_bar: Gtk.Widget) -> Gtk.Widget:
    """Styled as if it were an app window's title bar."""
    box = Gtk.Box()
    box.add_css_class(PROTON_APP_CSS_CLASS)
    box.set_size_request(MainWindow.WIDTH, NATURAL)
    header_bar.set_hexpand(True)
    box.append(header_bar)
    return box


@register_demo("app-bar", label="main-window")
def app_bar_main_window() -> Gtk.Widget:
    """The main window's bar: menu button, title and window controls."""
    header_bar = HeaderBar(mock_controller(), mock_main_window(), MagicMock(name="OverlayWidget"))
    # The title comes from the window in the app.
    header_bar.set_title_widget(Gtk.Label(label="Proton VPN", css_classes=["title"]))
    return _in_app_window(header_bar)


@register_demo("app-bar", label="dialog")
def app_bar_dialog() -> Gtk.Widget:
    """A dialog's bar: title and close button."""
    header_bar = Gtk.HeaderBar()
    header_bar.set_decoration_layout(":close")
    header_bar.set_title_widget(Gtk.Label(label="Settings", css_classes=["title"]))
    return _in_app_window(header_bar)
