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


Tests for framed_like_app: reproducing the app's container chain around a
demo widget.
"""
from proton.vpn.app.gtk import Gtk
from proton.vpn.app.gtk.demo import sizing
from proton.vpn.app.gtk.demo.framing import framed_like_app
from proton.vpn.app.gtk.widgets.main.main_window import MainWindow


def test_reproduces_the_main_widget_content_layout_chain():
    """The names must match so the app's `#main-widget #content-layout` CSS applies."""
    child = Gtk.Label(label="x")

    wrapper = framed_like_app(child)

    content_layout = wrapper.get_first_child()
    assert wrapper.get_name() == "main-widget"
    assert content_layout.get_name() == "content-layout"
    assert content_layout.get_first_child() is child


def test_pins_width_to_the_main_window_column():
    width, _ = framed_like_app(Gtk.Label(label="x")).get_size_request()

    assert width == MainWindow.WIDTH


def test_height_left_natural_when_not_filling():
    wrapper = framed_like_app(Gtk.Label(label="x"), fill_height=False)

    _, height = wrapper.get_size_request()
    assert height == sizing.NATURAL  # height not pinned
    assert wrapper.get_first_child().get_vexpand() is False


def test_height_fills_window_content_area_when_filling():
    wrapper = framed_like_app(Gtk.Label(label="x"), fill_height=True)

    _, height = wrapper.get_size_request()
    header = Gtk.HeaderBar().measure(Gtk.Orientation.VERTICAL, sizing.UNCONSTRAINED)[1]
    # The window's content area is its height minus the header bar.
    assert height == MainWindow.HEIGHT - header
    assert wrapper.get_first_child().get_vexpand() is True
