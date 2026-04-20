"""
This module defines the server load widget.


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


class ServerLoad(Gtk.Box):
    """Displays the server load as a colored bar with a percentage label."""

    def __init__(self, load: int):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        self.set_name("server-load")

        self._bar = Gtk.LevelBar.new_for_interval(0, 100)
        self._bar.set_name("server-load-bar")
        self._bar.set_size_request(36, -1)
        self._bar.set_valign(Gtk.Align.CENTER)
        self.append(self._bar)

        self._label = Gtk.Label()
        self._label.set_width_chars(4)  # Reserve space for "100%"
        self._label.set_xalign(1.0)
        self.append(self._label)

        self.set_load(load)

    def set_load(self, load: int):
        """Sets the load percentage to be displayed."""
        self._bar.set_value(load)
        self._label.set_label(f"{load}%")
        self.set_tooltip_text(f"Server load is at {load}%")

        for cls in ("signal-danger", "signal-warning", "signal-success"):
            self._bar.remove_css_class(cls)

        if load > 90:
            self._bar.add_css_class("signal-danger")
        elif load > 75:
            self._bar.add_css_class("signal-warning")
        else:
            self._bar.add_css_class("signal-success")

    def get_label(self) -> str:
        """Returns the percentage label text."""
        return self._label.get_label()
