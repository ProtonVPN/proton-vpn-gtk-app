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


Tests for the app stylesheets: they parse without errors, load in the right
order, and only _primitives.css styles GTK widgets by type, with every rule
limited to .proton-app.
"""
from pathlib import Path
from typing import List

import pytest

from proton.vpn.app.gtk import Gtk
from proton.vpn.app.gtk.assets.style import MAIN_CSS, PRIMITIVES_CSS, app_css_paths

PROTON_APP_PREFIX = ".proton-app "


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

    assert selectors, f"No selectors read from {path.name}: has GTK's to_string() format changed?"
    return selectors


def test_stock_widget_rules_load_before_main_css():
    assert app_css_paths() == [PRIMITIVES_CSS, MAIN_CSS]


@pytest.mark.parametrize(
    "path", [PRIMITIVES_CSS, MAIN_CSS], ids=lambda p: p.name
)
def test_stylesheet_parses_without_errors(path):
    errors = []
    provider = Gtk.CssProvider()
    provider.connect(
        "parsing-error", lambda _provider, _section, error: errors.append(error.message)
    )

    provider.load_from_path(str(path))

    assert errors == []


def test_every_stock_widget_selector_is_scoped_to_proton_app():
    unscoped = [
        selector for selector in _selectors(PRIMITIVES_CSS)
        if not selector.startswith(PROTON_APP_PREFIX)
    ]

    assert unscoped == []


def test_no_bare_element_selectors_outside_the_stock_widget_stylesheet():
    """A selector starting with an element name (`button`, `label.x`) matches
    widgets in every window, including dialogs the app didn't create. Rules for
    GTK widget types belong in _primitives.css, starting with .proton-app.

    main.css imports the per-screen stylesheets, so this covers them too.
    """
    bare = [selector for selector in _selectors(MAIN_CSS) if selector[0].islower()]

    assert bare == []
