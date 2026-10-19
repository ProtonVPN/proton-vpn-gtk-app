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
from proton.vpn.app.gtk.demo.sizing import NATURAL
from proton.vpn.app.gtk.utils.entry import add_clear_icon
from proton.vpn.app.gtk.utils.window import PROTON_APP_CSS_CLASS
from proton.vpn.app.gtk.widgets.login.password_entry import PasswordEntry
from proton.vpn.app.gtk.widgets.vpn.info_button import info_menu_button

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
    """Put `grid` in a box with the app window's background colour.

    This shows the widgets on the same background as in the app: the box has
    the window's .proton-app class and GTK's background class.
    """
    for margin in ("top", "bottom", "start", "end"):
        getattr(grid, f"set_margin_{margin}")(_SPACING)
    box = Gtk.Box()
    box.add_css_class(PROTON_APP_CSS_CLASS)
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


_TOGGLE_STATES: List[Tuple[str, Callable[[Gtk.Widget], None]]] = [
    ("default", lambda w: None),
    ("hover", lambda w: _force(w, HOVER)),
    ("active", lambda w: _force(w, ACTIVE)),
    ("focus-visible", lambda w: _force(w, FOCUS_VISIBLE)),
    ("disabled", lambda w: w.set_sensitive(False)),
]


def _state_grid(rows: List[Tuple[str, Callable[[], Gtk.Widget]]]) -> Gtk.Widget:
    """One row per variant (e.g. off, on) and one column per state."""
    grid = Gtk.Grid(row_spacing=_SPACING, column_spacing=_SPACING)
    for column, (state, _) in enumerate(_TOGGLE_STATES, start=1):
        grid.attach(Gtk.Label(label=state), column, 0, 1, 1)
    for row, (caption, new_widget) in enumerate(rows, start=1):
        grid.attach(Gtk.Label(label=caption, xalign=0), 0, row, 1, 1)
        for column, (_, apply_state) in enumerate(_TOGGLE_STATES, start=1):
            widget = new_widget()
            widget.set_halign(Gtk.Align.CENTER)
            widget.set_valign(Gtk.Align.CENTER)
            apply_state(widget)
            grid.attach(widget, column, row, 1, 1)
    return _canvas(grid)


@register_demo("primitives", label="switch")
def switches() -> Gtk.Widget:
    """Switch, off and on, in each state."""
    return _state_grid([
        ("off", lambda: _switch(False)),
        ("on", lambda: _switch(True)),
    ])


@register_demo("primitives", label="checkbutton")
def checkbuttons() -> Gtk.Widget:
    """Checkbox, unchecked, checked and indeterminate, in each state."""
    return _state_grid([
        ("off", lambda: _check(False)),
        ("on", lambda: _check(True)),
        ("indeterminate", lambda: _check(False, inconsistent=True)),
    ])


@register_demo("primitives", label="radio")
def radios() -> Gtk.Widget:
    """Radio button, off and on, in each state."""
    return _state_grid([
        ("off", lambda: _radio(False)),
        ("on", lambda: _radio(True)),
    ])


_ENTRY_STATES: List[Tuple[str, Callable[[Gtk.Widget], None]]] = [
    ("empty", lambda w: w.set_text("")),
    ("filled", lambda w: None),
    ("hover", lambda w: _force(w, HOVER)),
    ("typing", lambda w: _force(w, FOCUS_WITHIN)),
    ("keyboard focus", lambda w: _force(w, FOCUS_WITHIN | FOCUS_VISIBLE)),
    ("selected text", lambda w: (_force(w, FOCUS_WITHIN), w.select_region(0, -1))),
    ("error", lambda w: w.add_css_class("input-error")),
    ("error + focus", lambda w: (w.add_css_class("input-error"), _force(w, FOCUS_WITHIN))),
    ("disabled", lambda w: w.set_sensitive(False)),
]


def _text_entry() -> Gtk.Entry:
    entry = Gtk.Entry(placeholder_text="Username", text="demo_user", width_chars=12)
    add_clear_icon(entry)
    return entry


def _password_entry() -> Gtk.Entry:
    entry = PasswordEntry()
    entry.set_placeholder_text("Password")
    entry.set_text("secret")
    entry.set_width_chars(12)
    return entry


@register_demo("primitives", label="entry")
def entries() -> Gtk.Widget:
    """Text fields, one column per kind and one row per state."""
    grid = Gtk.Grid(row_spacing=_SPACING, column_spacing=_SPACING)
    for row, (state, _) in enumerate(_ENTRY_STATES, start=1):
        grid.attach(Gtk.Label(label=state, xalign=0), 0, row, 1, 1)
    for column, (caption, new_entry) in enumerate(
        (("text", _text_entry), ("password", _password_entry)), start=1
    ):
        grid.attach(Gtk.Label(label=caption), column, 0, 1, 1)
        for row, (_, apply_state) in enumerate(_ENTRY_STATES, start=1):
            entry = new_entry()
            entry.set_can_focus(False)  # states are forced; real focus would add one
            apply_state(entry)
            grid.attach(entry, column, row, 1, 1)
    return _canvas(grid)


_GHOST_STATES: List[Tuple[str, Callable[[Gtk.MenuButton], None]]] = [
    ("default", lambda b: None),
    ("hover", lambda b: _force(b.get_first_child(), HOVER)),
    ("active", lambda b: _force(b.get_first_child(), ACTIVE)),
    ("open", lambda b: _force(b.get_first_child(), Gtk.StateFlags.CHECKED)),
    ("focus-visible", lambda b: _force(b.get_first_child(), FOCUS_VISIBLE)),
    ("disabled", lambda b: b.set_sensitive(False)),
]


@register_demo("primitives", label="ghost button")
def ghost_buttons() -> Gtk.Widget:
    """The info button, one column per state ("open" while its popover shows)."""
    grid = Gtk.Grid(row_spacing=_SPACING, column_spacing=_SPACING)
    for column, (state, apply_state) in enumerate(_GHOST_STATES):
        grid.attach(Gtk.Label(label=state), column, 0, 1, 1)
        button = info_menu_button(Gtk.Popover(), "Info")
        button.set_halign(Gtk.Align.CENTER)
        apply_state(button)
        grid.attach(button, column, 1, 1, 1)
    return _canvas(grid)


def _combo_button(combobox: Gtk.ComboBox) -> Gtk.Widget:
    """The toggle button that shows a dropdown's chosen option."""
    return combobox.get_first_child().get_first_child()


_DROPDOWN_STATES: List[Tuple[str, Callable[[Gtk.ComboBox], None]]] = [
    ("default", lambda c: None),
    ("hover", lambda c: _force(_combo_button(c), HOVER)),
    ("expanded", lambda c: _force(_combo_button(c), Gtk.StateFlags.CHECKED)),
    ("disabled", lambda c: c.set_sensitive(False)),
    ("keyboard focus", lambda c: _force(_combo_button(c), FOCUS_VISIBLE)),
]


class _ComboboxLookalike(Gtk.Box):
    """Boxes drawn with a dropdown menu's styles. The real menu is a separate
    window, which the screenshot can't capture."""
    __gtype_name__ = "ProtonDemoCombobox"


class _PopoverLookalike(Gtk.Box):
    __gtype_name__ = "ProtonDemoPopover"


class _ContentsLookalike(Gtk.Box):
    __gtype_name__ = "ProtonDemoPopoverContents"


class _ModelButtonLookalike(Gtk.Box):
    __gtype_name__ = "ProtonDemoModelButton"


_ComboboxLookalike.set_css_name("combobox")
_PopoverLookalike.set_css_name("popover")
_ContentsLookalike.set_css_name("contents")
_ModelButtonLookalike.set_css_name("modelbutton")

# GTK marks the current option selected, whether the pointer or the keyboard
# made it current.
_MENU_ITEM_STATES: List[Tuple[str, Callable[[Gtk.Widget], None]]] = [
    ("default", lambda i: None),
    ("hover", lambda i: _force(i, HOVER | Gtk.StateFlags.SELECTED)),
    ("disabled", lambda i: i.set_sensitive(False)),
    ("keyboard focus", lambda i: _force(i, FOCUS_VISIBLE | Gtk.StateFlags.SELECTED)),
]


def _dropdown_menu() -> Gtk.Widget:
    """A dropdown menu with one option in each state."""
    contents = _ContentsLookalike(orientation=Gtk.Orientation.VERTICAL)
    for state, apply_state in _MENU_ITEM_STATES:
        item = _ModelButtonLookalike()
        item.add_css_class("flat")
        item.append(Gtk.Label(label=state, xalign=0, hexpand=True))
        apply_state(item)
        contents.append(item)
    popover = _PopoverLookalike()
    popover.append(contents)
    combobox = _ComboboxLookalike()
    combobox.set_halign(Gtk.Align.START)
    combobox.append(popover)
    return combobox


@register_demo("primitives", label="dropdown")
def dropdowns() -> Gtk.Widget:
    """The dropdown field in each state, and its menu."""
    grid = Gtk.Grid(row_spacing=_SPACING, column_spacing=_SPACING)
    for column, (state, apply_state) in enumerate(_DROPDOWN_STATES):
        grid.attach(Gtk.Label(label=state), column, 0, 1, 1)
        combobox = Gtk.ComboBoxText()
        for option in ("Smart", "WireGuard", "OpenVPN"):
            combobox.append_text(option)
        combobox.set_active(0)
        apply_state(combobox)
        grid.attach(combobox, column, 1, 1, 1)
    grid.attach(Gtk.Label(label="menu", xalign=0), 0, 2, 1, 1)
    grid.attach(_dropdown_menu(), 0, 3, 2, 1)
    return _canvas(grid)


_SEGMENT_STATES: List[Tuple[str, Callable[[Gtk.StackSwitcher, Gtk.Stack], None]]] = [
    ("selected", lambda s, st: None),
    ("selected hover", lambda s, st: _force(s.get_first_child(), HOVER)),
    ("unselected", lambda s, st: st.set_visible_child_name("credits")),
    ("unselected hover",
     lambda s, st: (st.set_visible_child_name("credits"), _force(s.get_first_child(), HOVER))),
    ("pressed",
     lambda s, st: (st.set_visible_child_name("credits"), _force(s.get_first_child(), ACTIVE))),
    ("keyboard focus", lambda s, st: _force(s.get_first_child(), FOCUS_VISIBLE)),
    ("keyboard focus, unselected",
     lambda s, st: (
         st.set_visible_child_name("credits"), _force(s.get_first_child(), FOCUS_VISIBLE)
     )),
    ("disabled", lambda s, st: s.set_sensitive(False)),
]


@register_demo("primitives", label="segmented control")
def segmented_controls() -> Gtk.Widget:
    """A stack switcher, one row per state of its first segment."""
    grid = Gtk.Grid(row_spacing=_SPACING, column_spacing=_SPACING)
    for row, (state, apply_state) in enumerate(_SEGMENT_STATES):
        grid.attach(Gtk.Label(label=state, xalign=0), 0, row, 1, 1)
        stack = Gtk.Stack()
        for name, title in (("about", "About"), ("label", "Label"), ("credits", "Credits")):
            stack.add_titled(Gtk.Box(), name, title)
        switcher = Gtk.StackSwitcher(stack=stack)
        switcher.set_halign(Gtk.Align.START)
        apply_state(switcher, stack)
        grid.attach(switcher, 1, row, 1, 1)
    return _canvas(grid)


class _TooltipLookalike(Gtk.Box):
    """A box drawn with the tooltip styles. Real tooltips are separate windows,
    which the screenshot can't capture."""
    __gtype_name__ = "ProtonDemoTooltip"


_TooltipLookalike.set_css_name("tooltip")


@register_demo("primitives", label="tooltip")
def tooltips() -> Gtk.Widget:
    """A short and a wrapped tooltip."""
    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=_SPACING)
    for text in ("Copy", "Secure Core routes your connection through two servers "
                         "in different countries."):
        tooltip = _TooltipLookalike()
        tooltip.add_css_class("background")  # as on real tooltips
        tooltip.set_halign(Gtk.Align.START)
        label = Gtk.Label(label=text, wrap=True, max_width_chars=30, xalign=0)
        tooltip.append(label)
        box.append(tooltip)
    for margin in ("top", "bottom", "start", "end"):
        getattr(box, f"set_margin_{margin}")(_SPACING)
    canvas = Gtk.Box()
    canvas.add_css_class(PROTON_APP_CSS_CLASS)
    canvas.add_css_class("background")
    canvas.append(box)
    return canvas


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
    scrollbar.set_size_request(NATURAL, 120)
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
        ("primary", "secondary", "danger", "destructive-action", "link"), start=1
    ):
        grid.attach(Gtk.Label(label=f".{css_class}", xalign=0), 0, row, 1, 1)
        for column, (_, apply_state) in enumerate(_BUTTON_STATES, start=1):
            button = Gtk.Button(label="Button")
            button.add_css_class(css_class)
            apply_state(button)
            grid.attach(button, column, row, 1, 1)
    return _canvas(grid)
