"""Tests for HoverBox."""

from proton.vpn.app.gtk import Gtk
from proton.vpn.app.gtk.widgets.vpn.serverlist.city_view.hover_box import HoverBox


def test_hover_box_set_child_hides_child_by_default():
    """Hover box has content hidden when a child is set (hidden by default)."""
    box = HoverBox()

    box.set_child(Gtk.Label(label="Test"))

    assert not box.is_content_visible()


def test_hover_box_shows_content_when_parent_is_hovered():
    """When parent_for_hover is hovered (enter), the hover box content is visible."""
    box = HoverBox()
    box.set_child(Gtk.Label(label="Test"))

    box.on_parent_hover_enter()

    assert box.is_content_visible()


def test_hover_box_hides_content_when_parent_is_not_hovered_and_child_has_no_focus():
    """When pointer leaves the parent, and the child has no focus, the hover box content is hidden."""
    box = HoverBox()
    box.set_child(Gtk.Label(label="Test"))
    box.on_parent_hover_enter()  # simulate parent being hovered

    box.on_parent_hover_leave()  # simulate parent not being hovered

    assert not box.is_content_visible()


def test_hover_box_shows_content_when_child_gains_focus():
    """When the child gains focus, the hover box content is visible."""
    box = HoverBox()
    box.set_child(Gtk.Label(label="Test"))

    box.on_child_focus_enter()  # simulate child focus

    assert box.is_content_visible()

def test_hover_box_hides_content_when_child_loses_focus_and_parent_is_not_hovered():
    """When the child widget loses focus (and parent is not hovered), the hover box content is hidden."""
    box = HoverBox()
    box.set_child(Gtk.Button(label="Click"))
    box.on_child_focus_enter()  # simulate child gaining focus

    box.on_child_focus_leave()  # simulate child loosing focus

    assert not box.is_content_visible()
