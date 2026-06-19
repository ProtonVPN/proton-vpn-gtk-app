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


Reproduce the app's container context around a demo widget.

In the app, embeddable widgets (login, quick-connect, ...) don't stand alone:
they live inside MainWidget's "#main-widget > #content-layout" chain, which CSS
pads by 20px, and they're shown at the MainWindow's column width. A widget shown
bare misses that padding (its contents run edge-to-edge) and that width. A
modal, by contrast, is a self-contained window and needs no framing.
"""
from proton.vpn.app.gtk import Gtk
from proton.vpn.app.gtk.demo.sizing import NATURAL, UNCONSTRAINED
from proton.vpn.app.gtk.widgets.main.main_window import MainWindow


def framed_like_app(widget: Gtk.Widget, fill_height: bool = False) -> Gtk.Widget:
    """Wrap `widget` in the app's #main-widget > #content-layout chain.

    Naming the chain makes the app's `#main-widget #content-layout` rule
    (padding: 20px) match, insetting the widget exactly as in the app, and the
    wrapper is pinned to the MainWindow's column width.

    fill_height distinguishes the two kinds of embeddable widget:
      - True for a widget that fills the window (e.g. login): the wrapper is also
        pinned to the window's content height (window height minus the header
        bar), so the form spreads as it does in the app instead of collapsing.
      - False for a widget that's only a band within the window (e.g. quick-connect):
        the height is left natural.
    """
    content_layout = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
    content_layout.set_name("content-layout")
    content_layout.append(widget)

    main_widget = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
    main_widget.set_name("main-widget")
    main_widget.append(content_layout)

    if fill_height:
        content_layout.set_vexpand(True)  # fill the window height, as in the app
        header_height = Gtk.HeaderBar().measure(
            Gtk.Orientation.VERTICAL, UNCONSTRAINED
        )[1]
        main_widget.set_size_request(
            MainWindow.WIDTH, MainWindow.HEIGHT - header_height
        )
    else:
        main_widget.set_size_request(MainWindow.WIDTH, NATURAL)
    return main_widget
