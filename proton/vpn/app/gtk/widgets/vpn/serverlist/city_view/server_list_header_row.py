"""
Header row for the server list showing country count and info icon.


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

from dataclasses import dataclass
from pathlib import Path

from gi.repository import Gdk
from proton.vpn.app.gtk import Gtk
from proton.vpn.app.gtk.assets import icons
from proton.vpn.app.gtk.widgets.vpn.serverlist.icons import (
    P2PIcon,
    SecureCoreIcon,
    SmartRoutingIcon,
    TORIcon,
)
from proton.vpn.app.gtk.utils.safe_signal_connect import safe_signal_connect


@dataclass
class LegendItem:
    """Data for a single entry in the feature legend popover.

    Attributes:
        icon_cls: Icon widget class or instance to display.
        heading: Title text for the feature.
        description: Explanatory text for the feature.
        learn_more_url: Optional URL for a "Learn more" link, or None.
    """

    icon_cls: type[Gtk.Widget]
    heading: str
    description: str
    learn_more_url: str | None


_LEGEND_ITEMS: list[LegendItem] = [
    LegendItem(
        SmartRoutingIcon,
        "Smart routing",
        # nosemgrep: string-concat-in-list
        "This technology allows Proton VPN to provide higher speed and security in "
        "difficult-to-reach countries.",
        "https://protonvpn.com/support/how-smart-routing-works",
    ),
    LegendItem(
        SecureCoreIcon,
        "Secure Core",
        # nosemgrep: string-concat-in-list
        "Connect to your destination server through a second, maximum security VPN server. "
        "Slower, but more private.",
        "https://protonvpn.com/support/secure-core-vpn",
    ),
    LegendItem(
        P2PIcon,
        "P2P/BitTorrent",
        "These servers give the best performance for BitTorrent and file sharing.",
        "https://protonvpn.com/features/p2p-support",
    ),
    LegendItem(
        TORIcon,
        "Tor",
        "Connect to a Tor server to access hidden services and onion sites using any browser.",
        "https://protonvpn.com/support/tor-vpn",
    ),
]


class FeatureLegendPopover(Gtk.Popover):
    """Popover explaining the feature icons shown on server rows."""

    def __init__(self):
        super().__init__()
        self.set_name("feature-legend-popover")
        self.set_child(self._build_content())

    def _build_content(self) -> Gtk.Box:
        """Builds the full popover content (header + feature rows)."""
        main = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        main.set_spacing(0)
        main.append(self._build_header())
        main.append(self._build_feature_rows())
        return main

    def _on_close_clicked(self, _):
        self.popdown()

    def _build_header(self) -> Gtk.Box:
        """Builds the title bar with close button."""
        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        header.add_css_class("feature-legend-header")

        title = Gtk.Label(label="Features")
        title.add_css_class("dim-label")
        title.set_halign(Gtk.Align.START)
        title.set_hexpand(True)
        title.add_css_class("heading")
        header.append(title)

        close_btn = Gtk.Button()
        close_btn.set_icon_name("window-close-symbolic")
        close_btn.add_css_class("flat")
        close_btn.add_css_class("circular")
        close_btn.set_tooltip_text("Close")
        safe_signal_connect(close_btn, "clicked", self._on_close_clicked)
        header.append(close_btn)
        return header

    def _build_feature_rows(self) -> Gtk.Box:
        """Builds the content area with all feature legend rows."""
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        content.add_css_class("feature-legend-content")
        for item in _LEGEND_ITEMS:
            content.append(self._build_legend_row(
                item.icon_cls, item.heading, item.description, item.learn_more_url
            ))
        return content

    def _build_legend_row(
        self,
        icon_cls: type,
        heading_text: str,
        description_text: str,
        learn_more_url: str | None,
    ) -> Gtk.Box:
        """Builds a single feature legend row (icon + heading + description + optional link)."""
        icon = icon_cls()
        icon.add_css_class("feature-legend-icon")
        icon.set_halign(Gtk.Align.START)
        icon.set_valign(Gtk.Align.START)
        icon.set_hexpand(False)
        icon.set_size_request(16, 16)

        text_block = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        text_block.set_spacing(0)
        text_block.set_hexpand(True)
        text_block.append(self._build_heading_label(heading_text))
        text_block.append(self._build_description_label(description_text))
        if learn_more_url:
            text_block.append(self._build_learn_more_link(learn_more_url))

        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        row.add_css_class("feature-legend-row")
        row.append(icon)
        row.append(text_block)
        return row

    @staticmethod
    def _build_heading_label(text: str) -> Gtk.Label:
        """Builds a heading label for a legend item."""
        label = Gtk.Label(label=text)
        label.set_halign(Gtk.Align.START)
        label.set_wrap(True)
        label.add_css_class("heading")
        return label

    @staticmethod
    def _build_description_label(text: str) -> Gtk.Label:
        """Builds a description label for a legend item."""
        label = Gtk.Label(label=text)
        label.add_css_class("feature-legend-description")
        label.set_halign(Gtk.Align.START)
        label.set_wrap(True)
        label.set_max_width_chars(35)
        label.add_css_class("dim-label")
        return label

    @staticmethod
    def _build_learn_more_link(url: str) -> Gtk.LinkButton:
        """Builds a Learn more link button."""
        link = Gtk.LinkButton(uri=url, label="Learn more")
        link.set_halign(Gtk.Align.START)
        link.add_css_class("feature-legend-learn-more")
        return link


class ServerListHeaderRow(Gtk.Box):
    """Header row displaying country count on the left and an info icon on the right."""

    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL)
        self.set_name("server-list-header-row")

        self._count_label = Gtk.Label()
        self._count_label.set_halign(Gtk.Align.START)
        self._count_label.add_css_class("dim-label")
        self.prepend(self._count_label)

        self._info_button = Gtk.MenuButton()
        self._info_button.set_can_focus(False)
        self._info_button.set_has_frame(False)
        self._info_button.add_css_class("dim-label")
        self._info_button.add_css_class("server-list-header-info-icon")
        self._feature_legend_popover = FeatureLegendPopover()
        self._info_button.set_popover(self._feature_legend_popover)
        self._info_button.set_direction(Gtk.ArrowType.DOWN)
        self._info_button.set_always_show_arrow(False)
        self._info_button.set_cursor(Gdk.Cursor.new_from_name("pointer", None))
        pixbuf = icons.get(Path("info.svg"), width=18, height=18)
        info_icon = Gtk.Image.new_from_paintable(Gdk.Texture.new_for_pixbuf(pixbuf))
        info_icon.set_size_request(pixbuf.get_width(), pixbuf.get_height())
        self._info_button.set_child(info_icon)
        spacer = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        spacer.set_hexpand(True)
        self.append(spacer)
        self.append(self._info_button)

        self.set_count(0)

    def set_count(self, count: int) -> None:
        """Updates the displayed country count."""
        self._count_label.set_label(self._format_count(count))

    def _format_count(self, count: int) -> str:
        """Returns the formatted count string."""
        return f"All countries ({count})"
