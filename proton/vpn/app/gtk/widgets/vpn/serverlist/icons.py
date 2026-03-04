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
from __future__ import annotations
from pathlib import Path
from typing import Optional

from gi.repository import Gtk, Gdk, GdkPixbuf

from proton.vpn.app.gtk.assets import icons


class UnderMaintenanceIcon(Gtk.Image):
    """Icon displayed when a server/country is under maintenance."""
    def __init__(self, widget_under_maintenance: Optional[str] = None):
        super().__init__()
        pixbuf = icons.get(Path("maintenance-icon.svg"))
        texture = Gdk.Texture.new_for_pixbuf(pixbuf)
        self.set_from_paintable(texture)
        if widget_under_maintenance:
            help_text = f"{widget_under_maintenance} is under maintenance"
            self.set_tooltip_text(help_text)
            self.update_property([Gtk.AccessibleProperty.LABEL], [help_text])
        self.set_halign(Gtk.Align.END)
        self.set_hexpand(True)

    def set_help_text(self, help_text: str):
        """Sets the tooltip and accessible label text."""
        self.set_tooltip_text(help_text)
        self.update_property([Gtk.AccessibleProperty.LABEL], [help_text])


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
    """Icon displayed when a server or group supports Secure core.

    For a single server, pass entry and exit country names for the tooltip.
    For a group (e.g. country row), omit both for a generic tooltip.
    """
    def __init__(
        self,
        entry_country_name: Optional[str] = None,
        exit_country_name: Optional[str] = None
    ):
        super().__init__()
        pixbuf = icons.get(Path("servers/secure-core.svg"))
        texture = Gdk.Texture.new_for_pixbuf(pixbuf)
        self.set_from_paintable(texture)
        if entry_country_name and exit_country_name:
            help_text = (
                "Secure core server that "
                f"connects to {exit_country_name} through {entry_country_name}."
            )
        else:
            help_text = "Secure Core supported"
        self.set_tooltip_text(help_text)
        self.update_property([Gtk.AccessibleProperty.LABEL], [help_text])


class DoubleFlagIcon(Gtk.Image):
    """Two superposed flags composited into one image.

    Exit country (front) is slightly larger and placed at top-right.
    Entry country (back) is slightly smaller and placed at bottom-left.

    Canvas dimensions are derived from both flags:
      canvas_w = max(back_w, offset_x + front_w)
      canvas_h = max(front_h, offset_y + back_h)

    For front to visually dominate the height, keep offset_y + back_h <= front_h.
    """
    _FRONT_WIDTH = 24
    _FRONT_HEIGHT = 16
    _BACK_WIDTH = 18
    _BACK_HEIGHT = 12
    # How far right the front flag starts / how far down the back flag starts.
    _OFFSET_X = 12
    _OFFSET_Y = 10

    def __init__(self, exit_country_code: str, entry_country_code: str):
        super().__init__()

        back_pixbuf = self._load_flag_pixbuf(
            entry_country_code, self._BACK_WIDTH, self._BACK_HEIGHT
        )
        front_pixbuf = self._load_flag_pixbuf(
            exit_country_code, self._FRONT_WIDTH, self._FRONT_HEIGHT
        )

        canvas_w = self._FRONT_WIDTH + self._OFFSET_X
        canvas_h = self._BACK_HEIGHT + self._OFFSET_Y
        composite = GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, True, 8, canvas_w, canvas_h)
        composite.fill(0x00000000)

        # Back flag (entry country) at bottom-left.
        back_pixbuf.composite(
            composite,
            dest_x=0, dest_y=self._OFFSET_Y,
            dest_width=self._BACK_WIDTH, dest_height=self._BACK_HEIGHT,
            offset_x=0.0, offset_y=self._OFFSET_Y,
            scale_x=1.0, scale_y=1.0,
            interp_type=GdkPixbuf.InterpType.BILINEAR,
            overall_alpha=255,
        )
        # Front flag (exit country) at top-right, drawn on top.
        front_pixbuf.composite(
            composite,
            dest_x=self._OFFSET_X, dest_y=0,
            dest_width=self._FRONT_WIDTH, dest_height=self._FRONT_HEIGHT,
            offset_x=self._OFFSET_X, offset_y=0.0,
            scale_x=1.0, scale_y=1.0,
            interp_type=GdkPixbuf.InterpType.BILINEAR,
            overall_alpha=255,
        )

        self.set_from_paintable(Gdk.Texture.new_for_pixbuf(composite))

    @staticmethod
    def _load_flag_pixbuf(country_code: str, width: int, height: int) -> GdkPixbuf.Pixbuf:
        try:
            return icons.get(
                Path("flags") / f"{country_code.lower()}.svg",
                width=width, height=height, preserve_aspect_ratio=False,
            )
        except ValueError:
            return icons.get(
                Path("flags") / "placeholder.svg",
                width=width, height=height, preserve_aspect_ratio=False,
            )


class CityIcon(Gtk.Image):
    """Icon displayed on each city row."""
    def __init__(self):
        super().__init__()
        pixbuf = icons.get(Path("city.svg"))
        texture = Gdk.Texture.new_for_pixbuf(pixbuf)
        self.set_from_paintable(texture)


class CountryFlagIcon(Gtk.Image):
    """Flag displayed on each country row."""

    _cache = {}

    def __init__(self, country_code: str):
        super().__init__()

        try:
            pixbuf = icons.get(Path("flags") / f"{country_code.lower()}.svg")
        except ValueError:
            pixbuf = icons.get(Path("flags") / "placeholder.svg")
        texture = Gdk.Texture.new_for_pixbuf(pixbuf)
        self.set_from_paintable(texture)

    @classmethod
    def get_cached(cls, country_code: str) -> CountryFlagIcon:
        """Returns a cached CountryFlagIcon instance for the given country code."""
        country_code = country_code.lower()
        if country_code not in cls._cache:
            cls._cache[country_code] = CountryFlagIcon(country_code)
        return cls._cache[country_code]
