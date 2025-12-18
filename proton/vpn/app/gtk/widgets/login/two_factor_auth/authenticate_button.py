"""
This module defines the widget used to display the authenticate button.


Copyright (c) 2025 Proton AG

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
from gi.repository import Gtk

AUTHENTICATE_BUTTON_LABEL = "Authenticate"


class AuthenticateButton(Gtk.Button):
    """
    Implements the UI for the authenticate button.
    """

    def __init__(self, label: str = AUTHENTICATE_BUTTON_LABEL):
        super().__init__(label=label)
        self.add_css_class("primary")
        self.set_halign(Gtk.Align.FILL)
        self.set_hexpand(True)

    @property
    def enable(self) -> bool:
        """Returns if the authenticate button should be enabled or not."""
        return self.get_property("sensitive")

    @enable.setter
    def enable(self, newvalue: bool):
        """Sets if the authenticate button should be enabled or not."""
        self.set_property("sensitive", newvalue)
