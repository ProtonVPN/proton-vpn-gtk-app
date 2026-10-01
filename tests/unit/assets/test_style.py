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


Tests for the app stylesheets: they parse without errors, load with the right
priorities, and only the primitives stylesheets style GTK widgets by type, with
every rule limited to .proton-app.
"""
from pathlib import Path
from typing import List

import re

import pytest
from gi.repository import Gio

from proton.vpn.app.gtk import Gtk
from proton.vpn.app.gtk.assets.style import (
    MAIN_CSS, MAIN_PRIORITY, PALETTE_CSS, PALETTE_PRIORITY, PRIMITIVES_CSS,
    PRIMITIVES_PRIORITY, STYLE_PATH, app_css_paths,
)

PROTON_APP = ".proton-app"
THEME_RESET_CSS = STYLE_PATH / "_theme_reset.css"


def _selectors(path: Path) -> List[str]:
    """Every selector in the stylesheet, including rules from files it imports.

    GTK loads the file and to_string() writes it back out, so we don't parse the
    CSS ourselves. In that output comments are removed, imported files are
    included, and each rule starts at the left margin as `selector, selector {`.
    Lines starting with @ (colour definitions) or a space (declarations) are
    skipped.
    """
    provider = Gtk.CssProvider()
    provider.load_from_path(str(path))

    selectors = []
    for line in provider.to_string().splitlines():
        if line.endswith(" {") and not line.startswith((" ", "@")):
            selectors.extend(line[:-len(" {")].split(", "))
    return selectors


def _referenced_files(path: Path) -> List[str]:
    """Every file the stylesheet refers to with url(), as file:// URIs.

    GTK writes each url() out with the file's absolute URI.
    """
    provider = Gtk.CssProvider()
    provider.load_from_path(str(path))
    return re.findall(r"url\((file://[^)]+)\)", provider.to_string())


def _unscoped_selectors(path: Path) -> List[str]:
    return [
        selector for selector in _selectors(path)
        if selector != PROTON_APP and not selector.startswith(PROTON_APP + " ")
    ]


def _parsing_errors(path: Path) -> List[str]:
    errors = []
    provider = Gtk.CssProvider()
    provider.connect(
        "parsing-error", lambda _provider, _section, error: errors.append(error.message)
    )
    provider.load_from_path(str(path))
    return errors


def test_selectors_are_read_from_gtk_css_output():
    """The scoping tests pass trivially if no selectors are read, e.g. after a
    change to the format of GTK's to_string() output."""
    assert ".proton-app button.primary" in _selectors(PRIMITIVES_CSS)


def test_primitives_include_the_palette_and_theme_reset():
    """An @import that is commented out or misspelt still parses without errors."""
    provider = Gtk.CssProvider()
    provider.load_from_path(str(PRIMITIVES_CSS))
    css = provider.to_string()

    assert "@define-color focus-ring" in css
    assert "-gtk-icon-shadow: none;" in css


def test_primitives_load_below_and_the_palette_above_main_css():
    assert app_css_paths() == [
        (PRIMITIVES_CSS, PRIMITIVES_PRIORITY),
        (MAIN_CSS, MAIN_PRIORITY),
        (PALETTE_CSS, PALETTE_PRIORITY),
    ]
    assert PRIMITIVES_PRIORITY < MAIN_PRIORITY < PALETTE_PRIORITY


@pytest.mark.parametrize(
    "path",
    [PRIMITIVES_CSS, PALETTE_CSS, THEME_RESET_CSS, MAIN_CSS],
    ids=lambda p: p.name,
)
def test_stylesheet_parses_without_errors(path):
    assert _parsing_errors(path) == []


@pytest.mark.parametrize("path", [PRIMITIVES_CSS, THEME_RESET_CSS], ids=lambda p: p.name)
def test_every_stock_widget_selector_is_scoped_to_proton_app(path):
    assert _unscoped_selectors(path) == []


@pytest.mark.parametrize("path", [PRIMITIVES_CSS, MAIN_CSS], ids=lambda p: p.name)
def test_every_file_a_stylesheet_refers_to_exists(path):
    """GTK doesn't report a missing file when it loads the stylesheet."""
    missing = [
        uri for uri in _referenced_files(path)
        if not Gio.File.new_for_uri(uri).query_exists()
    ]

    assert missing == []


def test_icons_referenced_by_the_primitives_are_read_from_gtk_css_output():
    """The test above passes trivially if no files are read."""
    assert any(uri.endswith("/ic-checkmark-symbolic.svg")
               for uri in _referenced_files(PRIMITIVES_CSS))


def test_palette_only_defines_colours():
    """It's loaded above main.css, so any rule in it would override main.css."""
    assert _selectors(PALETTE_CSS) == []


def test_no_bare_element_selectors_outside_the_stock_widget_stylesheets():
    """A selector starting with an element name (`button`, `label.x`) matches
    widgets in every window, including dialogs the app didn't create. Rules for
    GTK widget types belong in the primitives stylesheets, starting with
    .proton-app.

    main.css imports the per-screen stylesheets, so this covers them too.
    """
    bare = [selector for selector in _selectors(MAIN_CSS) if selector[0].islower()]

    assert bare == []


# FreeRescope flag. Delete everything below when the flag is retired, along
# with _primitives_legacy.css.

LEGACY_PRIMITIVES_CSS = STYLE_PATH / "_primitives_legacy.css"


def test_legacy_primitives_parse_without_errors():
    assert _parsing_errors(LEGACY_PRIMITIVES_CSS) == []


def test_every_legacy_primitives_selector_is_scoped_to_proton_app():
    assert _unscoped_selectors(LEGACY_PRIMITIVES_CSS) == []
