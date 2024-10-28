"""
Server search entry module.


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
from __future__ import annotations

from gi.repository import GObject

from proton.vpn import logging

from proton.vpn.app.gtk import Gtk

logger = logging.getLogger(__name__)


class SearchEntry(Gtk.SearchEntry):
    """Widget used to filter server list based on user input."""
    def __init__(self):
        super().__init__()
        self.set_placeholder_text("Press Ctrl+F to search")
        self.connect("request-focus", lambda _: self.grab_focus())
        self.connect("unrealize", lambda _: self.reset())

    @GObject.Signal(name="request_focus", flags=GObject.SignalFlags.ACTION)
    def request_focus(self, _):
        """Emitting this signal requests input focus on the search text entry."""

    def reset(self):
        """Resets the widget UI."""
        self.set_text("")
