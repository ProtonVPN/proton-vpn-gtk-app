"""Tests for HoverStack."""

from proton.vpn.app.gtk import Gtk
from proton.vpn.app.gtk.widgets.vpn.serverlist.city_view.hover_stack import HoverStack


def test_hover_stack_shows_leave_child_by_default():
    """The leave child is shown by default after a hover child is set."""
    leave = Gtk.Box()
    stack = HoverStack(leave_child=leave, hover_child=Gtk.Button(label="Connect"))

    assert stack.get_visible_child() is leave


def test_hover_stack_shows_hover_child_when_parent_is_hovered():
    """When the parent is hovered (enter), the hover child is shown."""
    hover = Gtk.Button(label="Connect")
    stack = HoverStack(leave_child=Gtk.Box(), hover_child=hover)

    stack._on_hover_enter()

    assert stack.get_visible_child() is hover


def test_hover_stack_shows_leave_child_when_parent_is_not_hovered_and_child_has_no_focus():
    """When the pointer leaves the parent and the hover child has no focus, the leave child is shown."""
    leave = Gtk.Box()
    stack = HoverStack(leave_child=leave, hover_child=Gtk.Button(label="Connect"))
    stack._on_hover_enter()  # simulate parent being hovered

    stack._on_hover_leave()  # simulate parent not being hovered

    assert stack.get_visible_child() is leave


def test_hover_stack_shows_hover_child_when_focused():
    """When the stack receives keyboard focus, it switches to the hover child."""
    hover = Gtk.Button(label="Connect")
    stack = HoverStack(leave_child=Gtk.Box(), hover_child=hover)

    stack.do_focus(Gtk.DirectionType.TAB_FORWARD)

    assert stack.get_visible_child() is hover


def test_hover_stack_shows_leave_child_when_child_loses_focus_and_parent_is_not_hovered():
    """When the hover child loses focus and the parent is not hovered, the leave child is shown."""
    leave = Gtk.Box()
    stack = HoverStack(leave_child=leave, hover_child=Gtk.Button(label="Connect"))
    stack._on_hover_enter()   # hover to show hover child
    stack._on_hover_leave()   # leave hover — not hovered, no focus → leave child shown
    stack.do_focus(Gtk.DirectionType.TAB_FORWARD)  # simulate focus entering

    stack._on_child_focus_leave()  # simulate focus leaving

    assert stack.get_visible_child() is leave
