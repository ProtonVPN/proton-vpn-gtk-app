"""
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
from gi.repository import GdkPixbuf, Gtk

from proton.vpn.app.gtk.assets import ASSETS_PATH


class ProtonVPNLogo(Gtk.Image):
    """Proton VPN logo shown in the login widget."""
    def __init__(self):
        super().__init__()
        pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
            filename=str(ASSETS_PATH / "proton-vpn-logo.svg"),
            width=300,
            height=300,
            preserve_aspect_ratio=True
        )
        self.set_margin_top(25)
        self.set_margin_bottom(25)
        self.set_from_pixbuf(pixbuf)
