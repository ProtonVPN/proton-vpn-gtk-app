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


Tests for the launcher's sizing/layout internals — the behaviour the demo was
built for: fixed-size cells, one size per modal, faithful reparenting, and a
window that matches its content.
"""
import pytest

from proton.vpn.app.gtk import Gtk
from proton.vpn.app.gtk.demo import launcher
from proton.vpn.app.gtk.demo.sizing import UNCONSTRAINED

H = Gtk.Orientation.HORIZONTAL
V = Gtk.Orientation.VERTICAL


def _min_nat(widget, orientation):
    minimum, natural, _, _ = widget.measure(orientation, UNCONSTRAINED)
    return minimum, natural


def _natural(widget, orientation):
    return widget.measure(orientation, UNCONSTRAINED)[1]


def _cells(window):
    """The labelled-group cells laid out inside the gallery window."""
    child = window.get_child().get_child()  # ScrolledWindow -> Viewport or row
    row = child.get_child() if isinstance(child, Gtk.Viewport) else child
    cells = []
    cell = row.get_first_child()
    while cell is not None:
        cells.append(cell)
        cell = cell.get_next_sibling()
    return cells


# --- fixed_size: the exact-size lock that set_size_request can't do ---

def test_fixed_size_reports_exact_size_regardless_of_child():
    # A non-wrapping label whose natural size is far larger than the lock.
    child = Gtk.Label(label="a label that would like to be much wider than this")

    box = launcher.fixed_size(child, 40, 25)

    assert _min_nat(box, H) == (40, 40)  # capped, not just floored
    assert _min_nat(box, V) == (25, 25)


def test_fixed_size_never_expands():
    box = launcher.fixed_size(Gtk.Label(label="x"), 40, 25)

    assert box.get_hexpand() is False
    assert box.get_vexpand() is False


def test_fixed_size_holds_the_child():
    child = Gtk.Label(label="x")

    assert launcher.fixed_size(child, 40, 25).get_first_child() is child


# --- modal_content_size: one size, clamped up to content, across variants ---

def _window(default_size, content_request=None):
    window = Gtk.Window()
    window.set_default_size(*default_size)
    if content_request is not None:
        content = Gtk.Box()
        content.set_size_request(*content_request)
        window.set_child(content)
    return window


def test_modal_size_clamps_width_up_to_content_minimum():
    # Default is only 100 wide but the content needs 300; height stays at the
    # default since the content is shorter.
    window = _window((100, 80), content_request=(300, 50))

    assert launcher.modal_content_size([window]) == (300, 80)


def test_modal_size_clamps_height_up_to_content_natural():
    window = _window((100, 80), content_request=(150, 200))

    assert launcher.modal_content_size([window]) == (150, 200)


def test_modal_size_is_the_max_across_variants():
    wide = _window((100, 80), content_request=(300, 50))
    tall = _window((100, 80), content_request=(150, 200))

    # Width from `wide`, height from `tall` — every variant gets this one size.
    assert launcher.modal_content_size([wide, tall]) == (300, 200)


def test_modal_size_falls_back_to_default_without_content():
    window = _window((120, 90), content_request=None)

    assert launcher.modal_content_size([window]) == (120, 90)


def test_modal_size_of_no_windows_is_zero():
    assert launcher.modal_content_size([]) == (0, 0)


# --- embed_window: reparenting a modal while keeping its styling ---

def test_embed_window_reparents_copies_css_identity_and_sizes():
    window = Gtk.Window()
    window.set_name("test-modal")
    window.add_css_class("test-modal-class")
    content = Gtk.Label(label="hello")
    window.set_child(content)

    wrapper = launcher.embed_window(window, (200, 150))

    # Content lifted out of the window and rehosted in the wrapper.
    assert window.get_child() is None
    assert wrapper.get_first_child() is content
    # The window's CSS identity is copied so its styling still matches.
    assert wrapper.get_name() == "test-modal"
    assert "test-modal-class" in wrapper.get_css_classes()
    # Locked to the requested size, top-left.
    assert _min_nat(wrapper, H) == (200, 200)
    assert _min_nat(wrapper, V) == (150, 150)
    assert wrapper.get_halign() == Gtk.Align.START
    assert wrapper.get_valign() == Gtk.Align.START


# --- build_window: integration invariants on the real screens ---

@pytest.mark.parametrize("screen", ["nps-modal", "login", "bug-report", "quick-connect"])
def test_build_window_does_not_force_a_default_size(screen):
    """No set_default_size, so the window auto-sizes to its content."""
    width, height = launcher.build_window(screen).get_default_size()

    assert width <= 0 and height <= 0


@pytest.mark.parametrize("screen", ["nps-modal", "login", "bug-report", "quick-connect"])
def test_build_window_matches_its_content_size(screen):
    """The window's natural size equals its content's — no clipping, no dead space."""
    window = launcher.build_window(screen)
    content = window.get_child()

    assert _natural(window, H) == _natural(content, H)
    assert _natural(window, V) == _natural(content, V)


def test_modal_variants_are_shown_at_one_uniform_size():
    cells = _cells(launcher.build_window("nps-modal"))

    sizes = {(_natural(cell, H), _natural(cell, V)) for cell in cells}
    assert len(cells) > 1 and len(sizes) == 1


def test_widget_variants_share_one_width():
    cells = _cells(launcher.build_window("login"))

    widths = {_natural(cell, H) for cell in cells}
    assert len(cells) > 1 and len(widths) == 1
