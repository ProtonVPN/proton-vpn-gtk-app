"""
Marks the app's windows so the styles in _primitives.css apply to them.

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
from proton.vpn.app.gtk import Gtk

# Marks a window as one of the app's own, for styles that must not reach
# windows the app didn't create.
PROTON_APP_CSS_CLASS = "proton-app"


def register_proton_window(window: Gtk.Window) -> None:
    """Add the .proton-app class to `window`.

    Call this for every window and dialog the app creates. GTK styles each
    window separately: a class on one window does not reach another window,
    such as a dialog it opens. Popovers attached to widgets in a window do get
    that window's class.
    """
    window.add_css_class(PROTON_APP_CSS_CLASS)
