"""
A summary of the countries a free connection is auto-selected from, plus the
"Free connections" popover listing them in full.


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

from pathlib import Path
from typing import List

from gi.repository import Gdk

from proton.vpn.app.gtk import Gtk
from proton.vpn.app.gtk.assets import icons
from proton.vpn.app.gtk.controller import Controller
from proton.vpn.app.gtk.translator import C_
from proton.vpn.app.gtk.utils.country import country_name_sort_key, get_localized_country_name
from proton.vpn.app.gtk.utils.safe_signal_connect import safe_signal_connect

# The flags icon depicts this many countries, so the "+N" label only has to
# account for the remaining ones.
DEPICTED_COUNTRY_COUNT = 3

COUNTRIES_PER_ROW = 3

FLAG_WIDTH = 24
FLAG_HEIGHT = 16

TRIPLE_FLAGS_ICON_WIDTH = 56
TRIPLE_FLAGS_ICON_HEIGHT = 16

INFO_ICON_SIZE = 20

FREE_COUNTRIES_INFO_LABEL = C_(
    "tooltip",
    # Names the button opening the popover that lists the countries a free
    # connection can be assigned to. Also its screen reader name.
    "Free server locations"
)

FREE_COUNTRIES_DESCRIPTION = C_(
    "message",
    "Proton Free automatically connects you to the fastest free server "
    "available. This is usually the closest server to your location."
)


def _country_flag(country_code: str) -> Gtk.Picture:
    """A country flag at its full size: a Gtk.Image would clamp it to a square
    icon box.
    """
    try:
        pixbuf = icons.get(
            Path("flags") / f"{country_code.lower()}.svg",
            width=FLAG_WIDTH, height=FLAG_HEIGHT
        )
    except ValueError:
        pixbuf = icons.get(
            Path("flags") / "placeholder.svg", width=FLAG_WIDTH, height=FLAG_HEIGHT
        )
    picture = Gtk.Picture.new_for_paintable(Gdk.Texture.new_for_pixbuf(pixbuf))
    picture.set_can_shrink(False)
    picture.set_size_request(pixbuf.get_width(), pixbuf.get_height())
    picture.set_halign(Gtk.Align.CENTER)
    picture.set_valign(Gtk.Align.CENTER)
    return picture


def free_country_codes(server_list) -> List[str]:
    """Returns the codes of the countries with free servers, sorted by name."""
    if not server_list:
        return []

    codes = {
        server.exit_country for server in server_list
        if server.free and server.exit_country
    }
    return sorted(codes, key=country_name_sort_key)


class FreeCountriesPopover(Gtk.Popover):
    """Popover listing every country a free connection can be assigned to."""

    def __init__(self):
        super().__init__()
        self.set_name("free-countries-popover")

        self._count_label: Gtk.Label
        self._countries_grid: Gtk.Grid

        self.set_child(self._build_content())

    def _build_content(self) -> Gtk.Box:
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        content.add_css_class("free-countries-content")
        content.append(self._build_header())
        content.append(self._build_description_label())

        self._count_label = Gtk.Label()
        self._count_label.add_css_class("free-countries-count")
        self._count_label.set_halign(Gtk.Align.START)
        content.append(self._count_label)

        self._countries_grid = self._build_countries_grid()
        content.append(self._countries_grid)
        return content

    def _build_header(self) -> Gtk.Box:
        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        header.add_css_class("free-countries-header")

        title = Gtk.Label(label=C_("title", "Free connections"))
        title.add_css_class("heading")
        title.set_halign(Gtk.Align.START)
        title.set_hexpand(True)
        header.append(title)

        close_button = Gtk.Button()
        close_button.set_icon_name("window-close-symbolic")
        close_button.add_css_class("circular")
        close_button.add_css_class("free-countries-close")
        close_button.set_valign(Gtk.Align.CENTER)
        close_button.set_tooltip_text(C_("tooltip", "Close"))
        safe_signal_connect(close_button, "clicked", self._on_close_clicked)
        header.append(close_button)
        return header

    @staticmethod
    def _build_description_label() -> Gtk.Label:
        label = Gtk.Label(label=FREE_COUNTRIES_DESCRIPTION)
        label.add_css_class("free-countries-description")
        label.set_xalign(0)
        label.set_wrap(True)
        label.set_hexpand(True)
        label.set_halign(Gtk.Align.FILL)
        label.set_max_width_chars(48)
        return label

    @staticmethod
    def _build_countries_grid() -> Gtk.Grid:
        grid = Gtk.Grid()
        grid.set_row_spacing(16)
        grid.set_column_spacing(16)
        grid.set_halign(Gtk.Align.START)
        return grid

    def _on_close_clicked(self, _):
        self.popdown()

    @property
    def count_label(self) -> Gtk.Label:
        """The label counting the countries with free servers."""
        return self._count_label

    @property
    def countries_grid(self) -> Gtk.Grid:
        """The grid of flag/name entries, one per country with free servers."""
        return self._countries_grid

    def set_countries(self, country_codes: List[str]):
        """Replaces the listed countries, updating the count with them."""
        self._count_label.set_label(
            C_(
                "label",
                # {count} is the number of countries with free servers.
                "Free server locations ({count})"
            ).format(count=len(country_codes))
        )

        while (child := self._countries_grid.get_first_child()) is not None:
            self._countries_grid.remove(child)

        for position, country_code in enumerate(country_codes):
            row, column = divmod(position, COUNTRIES_PER_ROW)
            self._countries_grid.attach(
                self._build_country_entry(country_code),
                column=column, row=row, width=1, height=1
            )

    @staticmethod
    def _build_country_entry(country_code: str) -> Gtk.Box:
        entry = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        entry.add_css_class("free-countries-entry")

        flag = _country_flag(country_code)
        flag.set_valign(Gtk.Align.CENTER)
        entry.append(flag)

        name = Gtk.Label(label=get_localized_country_name(country_code))
        name.set_halign(Gtk.Align.START)
        entry.append(name)
        return entry


class FreeCountriesSummary(Gtk.Box):
    """Condensed view of the countries a free connection is drawn from."""

    def __init__(self, controller: Controller):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL)
        self.set_name("free-countries-summary")
        self.set_halign(Gtk.Align.START)
        self.set_valign(Gtk.Align.CENTER)

        self._controller = controller

        self.append(Gtk.Label(label=C_("label", "Auto-selected from")))
        self.append(self._build_flags_icon())

        self._extra_count_label = Gtk.Label()
        self._extra_count_label.set_visible(False)
        self.append(self._extra_count_label)

        self._popover = FreeCountriesPopover()

        self._info_button = self._build_info_button(self._popover)
        self.append(self._info_button)

    @staticmethod
    def _build_flags_icon() -> Gtk.Picture:
        pixbuf = icons.get(
            Path("connection-status/free-countries.svg"),
            width=TRIPLE_FLAGS_ICON_WIDTH, height=TRIPLE_FLAGS_ICON_HEIGHT
        )
        # A Gtk.Image would scale this down to a square icon size; Gtk.Picture
        # draws it at its own proportions.
        picture = Gtk.Picture.new_for_paintable(Gdk.Texture.new_for_pixbuf(pixbuf))
        picture.set_can_shrink(False)
        picture.set_size_request(pixbuf.get_width(), pixbuf.get_height())
        picture.set_valign(Gtk.Align.CENTER)
        return picture

    @staticmethod
    def _build_info_button(popover: Gtk.Popover) -> Gtk.MenuButton:
        button = Gtk.MenuButton()
        button.add_css_class("free-countries-info")
        # Named explicitly: its only child is a picture, so there is no
        # text for a screen reader to use.
        button.set_tooltip_text(FREE_COUNTRIES_INFO_LABEL)
        button.update_property(
            [Gtk.AccessibleProperty.LABEL], [FREE_COUNTRIES_INFO_LABEL]
        )
        button.set_has_frame(False)
        button.set_popover(popover)
        button.set_direction(Gtk.ArrowType.DOWN)
        button.set_always_show_arrow(False)
        button.set_cursor(Gdk.Cursor.new_from_name("pointer", None))
        pixbuf = icons.get(Path("info.svg"), width=INFO_ICON_SIZE, height=INFO_ICON_SIZE)
        icon = Gtk.Picture.new_for_paintable(Gdk.Texture.new_for_pixbuf(pixbuf))
        icon.set_can_shrink(False)
        icon.set_size_request(pixbuf.get_width(), pixbuf.get_height())
        icon.set_halign(Gtk.Align.CENTER)
        icon.set_valign(Gtk.Align.CENTER)
        button.set_child(icon)
        return button

    @property
    def extra_count_label(self) -> Gtk.Label:
        """The label counting the countries the flags icon doesn't depict."""
        return self._extra_count_label

    @property
    def info_button(self) -> Gtk.MenuButton:
        """The button opening the "Free connections" popover."""
        return self._info_button

    @property
    def popover(self) -> FreeCountriesPopover:
        """The "Free connections" popover."""
        return self._popover

    def refresh(self):
        """Updates the summary and its popover from the current server list."""
        country_codes = free_country_codes(self._controller.server_list)

        extra_count = len(country_codes) - DEPICTED_COUNTRY_COUNT
        self._extra_count_label.set_visible(extra_count > 0)
        if extra_count > 0:
            self._extra_count_label.set_label(
                C_(
                    "label",
                    # {count} is how many more countries there are than the
                    # ones shown in the flags icon next to this label.
                    "+{count}"
                ).format(count=extra_count)
            )

        self._popover.set_countries(country_codes)
