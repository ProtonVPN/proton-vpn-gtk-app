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
        self._label = Gtk.Label.new()
        self._spinner = Gtk.Spinner.new()
        self._spinner.set_property("height-request", 50)

        # Another container had to be created to be able to vertically center
        # the content.
        self._centered_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        self._centered_container.show()

        self._centered_container.pack_start(self._label, expand=False, fill=False, padding=0)
        self._centered_container.pack_start(self._spinner, expand=False, fill=False, padding=0)
        self._centered_container.set_valign(Gtk.Align.CENTER)

        self.pack_start(self._centered_container, expand=True, fill=True, padding=0)
        # Adding the background class (which is a GTK class) gives the default
        # background color to this widget. This is needed as otherwise the widget
        # background is transparent, but the intended use of this widget is to
        # hide other widgets while an action is ongoing.
        self.get_style_context().add_class("background")
        self._label.show()
        self._spinner.show()
        self.set_no_show_all(True)

    def show(self, message: str):  # pylint: disable=arguments-differ
        """Shows the loading screen to the user."""
        self._label.set_label(message)
        self._spinner.start()
        Gtk.Box.show(self)

    def hide(self):  # pylint: disable=arguments-differ
        """Hides the loading widget from the user."""
        self._spinner.stop()
        self._label.set_label("")
        Gtk.Box.hide(self)
