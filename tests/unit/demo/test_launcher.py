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
import shutil
import struct
import tempfile
from pathlib import Path

import pytest
from gi.repository import GLib

from proton.vpn.app.gtk import Gtk
from proton.vpn.app.gtk.demo import discovery, launcher
from proton.vpn.app.gtk.demo.launcher import _snapshot_supported
from proton.vpn.app.gtk.demo.sizing import UNCONSTRAINED
from tests.unit.testing_utils import process_gtk_events

_requires_snapshot = pytest.mark.skipif(
    not _snapshot_supported(),
    reason="PyGObject cannot marshal GskRenderNode subclasses on this platform",
)

# Ensure demo screens are registered regardless of test collection order.
discovery.load_demo_screens()

H = Gtk.Orientation.HORIZONTAL
V = Gtk.Orientation.VERTICAL


def _min_nat(widget, orientation):
    minimum, natural, _, _ = widget.measure(orientation, UNCONSTRAINED)
    return minimum, natural


def _natural(widget, orientation):
    return widget.measure(orientation, UNCONSTRAINED)[1]


def _cells(row):
    """The labelled-group cells laid out inside the gallery row."""
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
    width, height = launcher.build_window(screen).window.get_default_size()

    assert width <= 0 and height <= 0


@pytest.mark.parametrize("screen", ["nps-modal", "login", "bug-report", "quick-connect"])
def test_build_window_matches_its_content_size(screen):
    """The window's natural size equals its content's — no clipping, no dead space."""
    gallery = launcher.build_window(screen)
    content = gallery.window.get_child()

    assert _natural(gallery.window, H) == _natural(content, H)
    assert _natural(gallery.window, V) == _natural(content, V)


def test_modal_variants_are_shown_at_one_uniform_size():
    cells = _cells(launcher.build_window("nps-modal").row)

    sizes = {(_natural(cell, H), _natural(cell, V)) for cell in cells}
    assert len(cells) > 1 and len(sizes) == 1


def test_widget_variants_share_one_width():
    cells = _cells(launcher.build_window("login").row)

    widths = {_natural(cell, H) for cell in cells}
    assert len(cells) > 1 and len(widths) == 1


# --- screenshot ---
#
# These drive show() — the same function DemoApp.do_activate() calls — which
# builds the window, schedules the after-paint capture, and destroys it.
#
# add_window() (called inside show()) is only valid once GApplication::startup
# has fired, which happens inside app.run(). Every test writes into shm_path, a
# directory verified to be tmpfs, so we never write to disk.

def _mount_fstype(path):
    """The filesystem type of the mount point containing `path`."""
    path = str(Path(path).resolve())
    best_mount_point, best_fstype = "", None
    with open("/proc/mounts", encoding="utf-8") as mounts:
        for line in mounts:
            mount_point, fstype = line.split()[1:3]
            if path.startswith(mount_point) and len(mount_point) > len(best_mount_point):
                best_mount_point, best_fstype = mount_point, fstype
    return best_fstype


@pytest.fixture
def shm_path():
    """A directory verified to be tmpfs (RAM-backed), so writes into it never
    reach a real disk. Skips rather than silently falling back if /dev/shm
    isn't tmpfs on this host.
    """
    if _mount_fstype("/dev/shm") != "tmpfs":
        pytest.skip("/dev/shm is not tmpfs on this host")
    path = Path(tempfile.mkdtemp(dir="/dev/shm"))
    try:
        yield path
    finally:
        shutil.rmtree(path)


def _png_dimensions(path):
    """Read width and height from a PNG file's IHDR chunk without an image library."""
    with open(path, 'rb') as f:
        f.read(16)  # 8-byte signature + 4-byte IHDR length + 4-byte "IHDR" type
        width = struct.unpack('>I', f.read(4))[0]
        height = struct.unpack('>I', f.read(4))[0]
    return width, height


def _run_show_with_screenshot(screen_name, out_path, timeout_ms=2000):
    """Runs show() for screen_name with a screenshot path via a real
    Gtk.Application, then waits for the window to be destroyed.

    Returns (natural_size, destroyed): natural_size is the gallery row's
    {"width", "height"}, measured right after show() returns and before the
    async capture runs; destroyed is True if the window's "destroy" signal
    fired before the safety timeout.
    """
    destroyed = []
    natural_size = {}

    def on_activate(app):
        window = launcher.show(app, screen_name, screenshot_path=str(out_path))
        row = window.get_child().get_child()  # ScrolledWindow -> row
        natural_size["width"] = row.measure(H, UNCONSTRAINED)[1]
        natural_size["height"] = row.measure(V, natural_size["width"])[1]
        window.connect("destroy", lambda _: destroyed.append(True))

    app = Gtk.Application()
    app.connect("activate", on_activate)
    GLib.timeout_add(interval=timeout_ms, function=app.quit)  # safety net against a hang
    app.run()
    process_gtk_events()

    return natural_size, bool(destroyed)


@_requires_snapshot
def test_screenshot_writes_png(shm_path):  # pylint: disable=redefined-outer-name
    """A PNG file is written at the specified path, and the window is destroyed."""
    out = shm_path / "shot.png"

    _, destroyed = _run_show_with_screenshot("login", out)

    assert destroyed
    assert out.is_file()


@_requires_snapshot
def test_screenshot_creates_parent_directories(shm_path):  # pylint: disable=redefined-outer-name
    """Missing parent directories are created before writing."""
    out = shm_path / "a" / "b" / "shot.png"

    _, destroyed = _run_show_with_screenshot("login", out)

    assert destroyed
    assert out.is_file()


@_requires_snapshot
def test_screenshot_dimensions_match_natural_size(shm_path):  # pylint: disable=redefined-outer-name
    """The PNG is the row's full natural size, not the screen-constrained viewport size."""
    out = shm_path / "shot.png"

    natural_size, destroyed = _run_show_with_screenshot("login", out)

    assert destroyed
    assert _png_dimensions(out) == (natural_size["width"], natural_size["height"])
