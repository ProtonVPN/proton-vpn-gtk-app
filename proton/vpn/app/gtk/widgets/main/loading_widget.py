"""
This module defines the Loading widget. This widget is responsible for displaying
the loading screen.


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

from proton.vpn.app.gtk import Gtk


class LoadingWidget(Gtk.Box):
    """Loading widget responsible for displaying loading status
    to the user."""

    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self._label = Gtk.Label(label="Loading app...")
        self.pack_start(self._label, expand=True, fill=True, padding=0)
        # Adding the background class (which is a GTK class) gives the default
        # background color to this widget. This is needed as otherwise the widget
        # background is transparent, but the intended use of this widget is to
        # hide other widgets while an action is ongoing.
        self.get_style_context().add_class("background")
        self.set_no_show_all(True)

    def show(self):  # pylint: disable=W0221
        """Shows the loading screen to the user."""
        self._label.show()
        Gtk.Box.show(self)
