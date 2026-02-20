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
"""
from __future__ import annotations

from gi.repository import GLib

from proton.vpn.app.gtk import Gtk


class ConnectButton(Gtk.Button):
    """Connect button that appears when hovering over a server location header."""

    def __init__(self, label: str = None):
        super().__init__()

        if label:
            self.set_label(label)

        self.add_css_class("connect-button")

        self.set_transparent(True)

        self._clicked_signal_id = None

        self.connect("realize", self._on_realize)
        self.connect("unrealize", self._on_unrealize)

    def set_transparent(self, transparent: bool):
        """Sets transparency using CSS classes."""
        if transparent:
            self.add_css_class("transparent")
        else:
            self.remove_css_class("transparent")

    def _on_realize(self, _widget):
        """Called when widget is realized."""
        # Remove focus after clicking so button hides when hovering other widgets
        def on_clicked(_button):
            def remove_focus():
                parent = self.get_parent()
                parent.set_can_focus(True)
                parent.set_focusable(True)
                parent.grab_focus()

            # Use idle_add to ensure this runs after the click handler
            GLib.idle_add(remove_focus)

        self._clicked_signal_id = self.connect("clicked", on_clicked)

        # This handles the case where focus was set before the widget was realized
        if self.has_focus():
            self.set_transparent(False)

    def _on_unrealize(self, _widget):
        """Called when widget is unrealized."""
        if self._clicked_signal_id is not None:
            self.disconnect(self._clicked_signal_id)
            self._clicked_signal_id = None
