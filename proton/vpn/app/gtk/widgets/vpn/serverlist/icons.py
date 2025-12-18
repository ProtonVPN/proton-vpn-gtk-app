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


class UnderMaintenanceIcon(Gtk.Image):
    """Icon displayed when a server/country is under maintenance."""
    def __init__(self, widget_under_maintenance: str):
        super().__init__()
        pixbuf = icons.get(Path("maintenance-icon.svg"))
        texture = Gdk.Texture.new_for_pixbuf(pixbuf)
        self.set_from_paintable(texture)
        help_text = f"{widget_under_maintenance} is under maintenance"
        self.set_tooltip_text(help_text)
        self.update_property([Gtk.AccessibleProperty.LABEL], [help_text])
        self.set_halign(Gtk.Align.END)
        self.set_hexpand(True)


class SmartRoutingIcon(Gtk.Image):
    """Icon displayed when smart routing is used."""
    def __init__(self):
        super().__init__()
        pixbuf = icons.get(Path("servers/smart-routing.svg"))
        texture = Gdk.Texture.new_for_pixbuf(pixbuf)
        self.set_from_paintable(texture)
        help_text = "Smart routing is used"
        self.set_tooltip_text(help_text)
        self.update_property([Gtk.AccessibleProperty.LABEL], [help_text])


class StreamingIcon(Gtk.Image):
    """Icon displayed when a server supports streaming."""
    def __init__(self):
        super().__init__()
        pixbuf = icons.get(Path("servers/streaming.svg"))
        texture = Gdk.Texture.new_for_pixbuf(pixbuf)
        self.set_from_paintable(texture)
        help_text = "Streaming supported"
        self.set_tooltip_text(help_text)
        self.update_property([Gtk.AccessibleProperty.LABEL], [help_text])


class P2PIcon(Gtk.Image):
    """Icon displayed when a server supports P2P."""
    def __init__(self):
        super().__init__()
        pixbuf = icons.get(Path("servers/p2p.svg"))
        texture = Gdk.Texture.new_for_pixbuf(pixbuf)
        self.set_from_paintable(texture)
        help_text = "P2P/BitTorrent supported"
        self.set_tooltip_text(help_text)
        self.update_property([Gtk.AccessibleProperty.LABEL], [help_text])


class TORIcon(Gtk.Image):
    """Icon displayed when a server supports TOR."""
    def __init__(self):
        super().__init__()
        pixbuf = icons.get(Path("servers/tor.svg"))
        texture = Gdk.Texture.new_for_pixbuf(pixbuf)
        self.set_from_paintable(texture)
        help_text = "TOR supported"
        self.set_tooltip_text(help_text)
        self.update_property([Gtk.AccessibleProperty.LABEL], [help_text])


class SecureCoreIcon(Gtk.Image):
    """Icon displayed when a server supports Secure core.

    Since Secure core servers have a different exit country from the entry
    country, for accessibility purposes both entry and exit countries must be
    passed.
    """
    def __init__(self, entry_country_name: str, exit_country_name: str):
        super().__init__()
        pixbuf = icons.get(Path("servers/secure-core.svg"))
        texture = Gdk.Texture.new_for_pixbuf(pixbuf)
        self.set_from_paintable(texture)
        help_text = "Secure core server that "\
            f"connects to {exit_country_name} through {entry_country_name}."
        self.set_tooltip_text(help_text)
        self.update_property([Gtk.AccessibleProperty.LABEL], [help_text])
