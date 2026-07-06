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
from pathlib import Path

from gi.repository import Gtk, Gdk

from proton.vpn.app.gtk.assets import icons


class ProtonVPNLogo(Gtk.Picture):
    """Proton VPN logo shown in the login widget."""
    LOGO_WIDTH = 320

    def __init__(self):
        super().__init__()
        self.set_name("login-logo")
        self.set_hexpand(False)
        self.set_vexpand(False)
        self.set_halign(Gtk.Align.CENTER)
        self.set_valign(Gtk.Align.CENTER)
        self.set_can_shrink(False)

        pixbuf = icons.get(
            Path("proton-vpn-logo.svg"),
            width=self.LOGO_WIDTH,
            preserve_aspect_ratio=True
        )
        texture = Gdk.Texture.new_for_pixbuf(pixbuf)
        self.set_paintable(texture)


class TwoFactorAuthProtonVPNLogo(Gtk.Picture):
    """Proton VPN logo shown in the login widget."""
    LOGO_WIDTH = 200

    def __init__(self):
        super().__init__()
        self.set_name("two-factor-auth-vpn-logo")
        self.set_hexpand(False)
        self.set_vexpand(False)
        self.set_halign(Gtk.Align.CENTER)
        self.set_valign(Gtk.Align.START)
        self.set_can_shrink(False)

        pixbuf = icons.get(
            Path("proton-vpn-logo.svg"),
            width=self.LOGO_WIDTH,
            preserve_aspect_ratio=True
        )
        texture = Gdk.Texture.new_for_pixbuf(pixbuf)
        self.set_paintable(texture)


class SecurityKeyLogo(Gtk.Picture):
    """Proton VPN logo shown in the login widget."""
    LOGO_WIDTH = 400

    def __init__(self):
        super().__init__()
        self.set_name("security-key-logo")
        self.set_hexpand(False)
        self.set_vexpand(False)
        self.set_halign(Gtk.Align.CENTER)
        self.set_valign(Gtk.Align.CENTER)

        pixbuf = icons.get(
            Path("security-key.svg"),
            width=self.LOGO_WIDTH,
            preserve_aspect_ratio=True
        )
        texture = Gdk.Texture.new_for_pixbuf(pixbuf)
        self.set_paintable(texture)
