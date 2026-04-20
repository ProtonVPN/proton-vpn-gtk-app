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
from typing import ClassVar, Dict, Optional

from gi.repository import Gtk, Gdk, GdkPixbuf

from proton.vpn.app.gtk.assets import icons
from proton.vpn.app.gtk.utils.assertions import runtime_assert


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
        exit_country_name: Optional[str] = None,
        size: Optional[int] = None,
    ):
        super().__init__()
        if size is not None:
            pixbuf = icons.get(Path("servers/secure-core.svg"), width=size, height=size)
        else:
            pixbuf = icons.get(Path("servers/secure-core.svg"))
        texture = Gdk.Texture.new_for_pixbuf(pixbuf)
        self.set_from_paintable(texture)
        if size is not None:
            self.set_size_request(pixbuf.get_width(), pixbuf.get_height())
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

    Canvas dimensions:
      canvas_w = front_w + offset_x
      canvas_h = back_h + offset_y
    """
    _FRONT_WIDTH = 36
    _FRONT_HEIGHT = 24
    _BACK_WIDTH = 27
    _BACK_HEIGHT = 18
    # How far right the front flag starts / how far down the back flag starts.
    _OFFSET_X = 18
    _OFFSET_Y = 15

    def __init__(self, exit_country_code: str, entry_country_code: str):
        super().__init__()

        front_w = self._FRONT_WIDTH
        front_h = self._FRONT_HEIGHT
        back_w = self._BACK_WIDTH
        back_h = self._BACK_HEIGHT
        offset_x = self._OFFSET_X
        offset_y = self._OFFSET_Y

        back_pixbuf = self._load_flag_pixbuf(entry_country_code, back_w, back_h)
        front_pixbuf = self._load_flag_pixbuf(exit_country_code, front_w, front_h)

        canvas_w = front_w + offset_x
        canvas_h = back_h + offset_y
        composite = GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, True, 8, canvas_w, canvas_h)
        runtime_assert(composite is not None, "Failed to create Pixbuf canvas")
        composite.fill(0x00000000)

        # Back flag (entry country) at bottom-left.
        back_pixbuf.composite(
            composite,
            dest_x=0, dest_y=offset_y,
            dest_width=back_w, dest_height=back_h,
            offset_x=0.0, offset_y=offset_y,
            scale_x=1.0, scale_y=1.0,
            interp_type=GdkPixbuf.InterpType.BILINEAR,
            overall_alpha=255,
        )
        # Front flag (exit country) at top-right, drawn on top.
        front_pixbuf.composite(
            composite,
            dest_x=offset_x, dest_y=0,
            dest_width=front_w, dest_height=front_h,
            offset_x=offset_x, offset_y=0.0,
            scale_x=1.0, scale_y=1.0,
            interp_type=GdkPixbuf.InterpType.BILINEAR,
            overall_alpha=255,
        )

        scaled = composite.scale_simple(
            CountryFlagIcon._FLAG_WIDTH, CountryFlagIcon._FLAG_HEIGHT,
            GdkPixbuf.InterpType.BILINEAR
        )
        self.set_from_paintable(Gdk.Texture.new_for_pixbuf(scaled))
        self.set_size_request(CountryFlagIcon._FLAG_WIDTH, CountryFlagIcon._FLAG_HEIGHT)

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


class LocationIcon(Gtk.Image):
    """Icon displayed on each location row."""

    SIZE = 24

    def __init__(self):
        super().__init__()
        pixbuf = icons.get(Path("location.svg"), width=self.SIZE, height=self.SIZE)
        texture = Gdk.Texture.new_for_pixbuf(pixbuf)
        self.set_from_paintable(texture)
        self.set_size_request(pixbuf.get_width(), pixbuf.get_height())


class CountryFlagIcon(Gtk.Image):
    """Flag displayed on each country row."""

    _FLAG_WIDTH = 24
    _FLAG_HEIGHT = 16
    _cache: ClassVar[Dict[str, CountryFlagIcon]] = {}

    def __init__(self, country_code: str):
        super().__init__()

        try:
            pixbuf = icons.get(
                Path("flags") / f"{country_code.lower()}.svg",
                width=self._FLAG_WIDTH, height=self._FLAG_HEIGHT
            )
        except ValueError:
            pixbuf = icons.get(Path("flags") / "placeholder.svg")
        texture = Gdk.Texture.new_for_pixbuf(pixbuf)
        self.set_from_paintable(texture)
        self.set_size_request(pixbuf.get_width(), pixbuf.get_height())
