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


Demo of every GTK built-in widget styled by _primitives.css.

One group per widget type, and one row per state that _primitives.css has a
rule for. Hover, focus and pressed states are set with set_state_flags,
because a screenshot has no mouse or keyboard input to trigger them.
"""
from typing import Callable, List, Optional, Tuple

from proton.vpn.app.gtk import Gtk
from proton.vpn.app.gtk.demo.registry import register_demo

HOVER = Gtk.StateFlags.PRELIGHT
ACTIVE = Gtk.StateFlags.ACTIVE
FOCUS = Gtk.StateFlags.FOCUSED
FOCUS_VISIBLE = Gtk.StateFlags.FOCUSED | Gtk.StateFlags.FOCUS_VISIBLE
# FOCUS_WITHIN doesn't exist in older GTK versions; fall back to FOCUSED.
FOCUS_WITHIN = getattr(Gtk.StateFlags, "FOCUS_WITHIN", Gtk.StateFlags.FOCUSED)

_SPACING = 12


def _force(widget: Gtk.Widget, flags: Optional[Gtk.StateFlags]) -> Gtk.Widget:
    if flags is not None:
        widget.set_state_flags(flags, False)
    return widget


def _canvas(grid: Gtk.Grid) -> Gtk.Widget:
    """Put `grid` in a box with the theme's window background colour.

    This shows the widgets on the same background as in the app.
    """
    for margin in ("top", "bottom", "start", "end"):
        getattr(grid, f"set_margin_{margin}")(_SPACING)
    box = Gtk.Box()
    box.add_css_class("background")
    box.append(grid)
    return box


def _grid(rows: List[Tuple[str, Gtk.Widget]]) -> Gtk.Widget:
    """A two-column grid: the state's name, then the widget in that state."""
    grid = Gtk.Grid(row_spacing=_SPACING, column_spacing=_SPACING)
    for row, (caption, widget) in enumerate(rows):
        label = Gtk.Label(label=caption, xalign=0)
        grid.attach(label, 0, row, 1, 1)
        widget.set_halign(Gtk.Align.START)
        widget.set_valign(Gtk.Align.CENTER)
        grid.attach(widget, 1, row, 1, 1)
    return _canvas(grid)


def _switch(active: bool, flags: Optional[Gtk.StateFlags] = None) -> Gtk.Switch:
    switch = Gtk.Switch()
    switch.set_active(active)
    return _force(switch, flags)


def _check(active: bool, inconsistent: bool = False,
           flags: Optional[Gtk.StateFlags] = None) -> Gtk.CheckButton:
    check = Gtk.CheckButton(label="Option")
    check.set_active(active)
    check.set_inconsistent(inconsistent)
    return _force(check, flags)


def _radio(active: bool, flags: Optional[Gtk.StateFlags] = None) -> Gtk.CheckButton:
    # A CheckButton in a group renders as a radio button.
    group = Gtk.CheckButton()
    radio = Gtk.CheckButton(label="Choice")
    radio.set_group(group)
    radio.set_active(active)
    return _force(radio, flags)


@register_demo("primitives", label="switch")
def switches() -> Gtk.Widget:
    """Switch track and handle, one row per state."""
    return _grid([
        ("off", _switch(False)),
        ("on", _switch(True)),
        ("on + hover", _switch(True, HOVER)),
        ("focus-visible", _switch(False, FOCUS_VISIBLE)),
    ])


@register_demo("primitives", label="checkbutton")
def checkbuttons() -> Gtk.Widget:
    """Checkbox, one row per state."""
    return _grid([
        ("off", _check(False)),
        ("on", _check(True)),
        ("indeterminate", _check(False, inconsistent=True)),
        ("on + hover", _check(True, flags=HOVER)),
        ("indeterminate + hover", _check(False, inconsistent=True, flags=HOVER)),
        ("focus-visible", _check(False, flags=FOCUS_VISIBLE)),
    ])


@register_demo("primitives", label="radio")
def radios() -> Gtk.Widget:
    """Radio button, one row per state."""
    return _grid([
        ("off", _radio(False)),
        ("on", _radio(True)),
        ("focus-visible", _radio(False, FOCUS_VISIBLE)),
    ])


def _entry(text: str = "", flags: Optional[Gtk.StateFlags] = None,
           select: bool = False) -> Gtk.Entry:
    entry = Gtk.Entry()
    entry.set_placeholder_text("Placeholder")
    entry.set_text(text)
    entry.set_width_chars(16)
    if select:
        entry.select_region(0, -1)
    return _force(entry, flags)


@register_demo("primitives", label="entry")
def entries() -> Gtk.Widget:
    """Entry border, focus ring and text selection."""
    return _grid([
        ("default", _entry()),
        ("focus-within", _entry("Typed text", FOCUS_WITHIN)),
        ("selected text", _entry("Selected text", FOCUS_WITHIN, select=True)),
    ])


def _find_node(widget: Gtk.Widget, css_name: str) -> Optional[Gtk.Widget]:
    """First descendant with the given CSS node name (e.g. a scrollbar's slider)."""
    child = widget.get_first_child()
    while child is not None:
        if child.get_css_name() == css_name:
            return child
        found = _find_node(child, css_name)
        if found is not None:
            return found
        child = child.get_next_sibling()
    return None


def _scrollbar(hover: bool = False) -> Gtk.Scrollbar:
    adjustment = Gtk.Adjustment(value=0, lower=0, upper=100, page_size=30)
    scrollbar = Gtk.Scrollbar(orientation=Gtk.Orientation.VERTICAL, adjustment=adjustment)
    scrollbar.set_size_request(-1, 120)
    if hover:
        slider = _find_node(scrollbar, "slider")
        if slider is not None:
            _force(slider, HOVER)
    return scrollbar


@register_demo("primitives", label="scrollbar")
def scrollbars() -> Gtk.Widget:
    """Scrollbar slider, default and hovered."""
    return _grid([
        ("default", _scrollbar()),
        ("slider hover", _scrollbar(hover=True)),
    ])


def _link_label(flags: Optional[Gtk.StateFlags] = None) -> Gtk.Label:
    label = Gtk.Label()
    label.set_markup('Read the <a href="https://protonvpn.com">privacy policy</a>')
    return _force(label, flags)


@register_demo("primitives", label="label")
def labels() -> Gtk.Widget:
    """Links, the focus ring on a label, and the .info, .error, .success and
    .signal-danger label classes."""
    rows: List[Tuple[str, Gtk.Widget]] = [
        ("link", _link_label()),
        ("focus-visible", _link_label(FOCUS_VISIBLE)),
    ]
    for css_class in ("info", "error", "success", "signal-danger"):
        label = Gtk.Label(label=f"label.{css_class}")
        label.add_css_class(css_class)
        rows.append((f".{css_class}", label))
    return _grid(rows)


_BUTTON_STATES: List[Tuple[str, Callable[[Gtk.Button], None]]] = [
    ("default", lambda b: None),
    ("hover", lambda b: _force(b, HOVER)),
    ("focus", lambda b: _force(b, FOCUS)),
    ("active", lambda b: _force(b, ACTIVE)),
    ("focus-visible", lambda b: _force(b, FOCUS_VISIBLE)),
    ("disabled", lambda b: b.set_sensitive(False)),
]


@register_demo("primitives", label="button")
def buttons() -> Gtk.Widget:
    """Each button class, one row per class and one column per state."""
    grid = Gtk.Grid(row_spacing=_SPACING, column_spacing=_SPACING)
    for column, (state, _) in enumerate(_BUTTON_STATES, start=1):
        grid.attach(Gtk.Label(label=state), column, 0, 1, 1)
    for row, css_class in enumerate(
        ("primary", "secondary", "danger", "destructive-action", "spaced", "link"), start=1
    ):
        grid.attach(Gtk.Label(label=f".{css_class}", xalign=0), 0, row, 1, 1)
        for column, (_, apply_state) in enumerate(_BUTTON_STATES, start=1):
            button = Gtk.Button(label="Button")
            button.add_css_class(css_class)
            apply_state(button)
            grid.attach(button, column, row, 1, 1)
    return _canvas(grid)
