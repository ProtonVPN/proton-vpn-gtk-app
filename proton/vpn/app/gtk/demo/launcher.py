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


Demo launcher: render a screen's registered factories in one gallery window.

A factory returns an embeddable widget or a top-level window. Embeddable
widgets go straight into the gallery; top-level windows (e.g. NPSSurveyModal,
BugReportDialog) can't be nested, so their content is lifted out and wrapped in
a box that mimics the window's CSS name and classes — keeping the modal's
styling while letting it sit in the gallery alongside everything else, with no
floating or overlapping windows.
"""
import os
from dataclasses import dataclass
from typing import List, Optional, Tuple

from gi.repository import Gdk, Graphene

from proton.vpn.app.gtk import Gtk
from proton.vpn.app.gtk.demo import registry
from proton.vpn.app.gtk.demo.sizing import NO_BASELINE, UNCONSTRAINED

_MARGIN = 18

# Minimum GTK version whose PyGObject binds GskRenderNode subclasses as
# Python return values. Below this, snapshot.to_node() either raises TypeError
# (Debian 12 / GTK 4.8) or — worse — corrupts state and segfaults the
# interpreter during GC (Ubuntu 22.04 / GTK 4.6).
# Gtk 4.14 (Ubuntu 24.04, Fedora, Arch, Debian 13)
# is the floor we've confirmed works; older distros no-op the screenshot path.
_MIN_SNAPSHOT_GTK = (4, 14)


def _snapshot_supported() -> bool:
    """True if PyGObject on this platform can marshal GskRenderNode subclasses.
    """
    return (Gtk.get_major_version(), Gtk.get_minor_version()) >= _MIN_SNAPSHOT_GTK


@dataclass
class DemoGallery:
    """The gallery window and its content row, as built by build_window()."""
    window: Gtk.Window
    row: Gtk.Box


# Loaded only in demo mode (see show()); never part of the app CSS.
#  - .demo-label: a monospace tag, clearly not part of the widget under test.
#  - .demo-bounds: just a soft drop shadow to show a widget's extent
_DEMO_CSS = b"""
.demo-label {
    font-family: monospace;
    font-size: 0.78em;
    font-weight: bold;
    color: rgba(255, 255, 255, 0.85);
    background-color: rgba(127, 127, 127, 0.20);
    border: 1px solid rgba(127, 127, 127, 0.35);
    border-radius: 6px;
    padding: 1px 8px;
    margin-bottom: 4px;
}
.demo-bounds {
    box-shadow: 0 1px 6px rgba(0, 0, 0, 0.55);
}
"""


def _load_demo_css() -> None:
    """Add the demo-only styling to the display. Not part of the app CSS."""
    display = Gdk.Display.get_default()
    if display is None:
        return
    provider = Gtk.CssProvider()
    provider.load_from_data(_DEMO_CSS)
    Gtk.StyleContext.add_provider_for_display(
        display, provider, Gtk.STYLE_PROVIDER_PRIORITY_USER
    )


def _take_screenshot(window: Gtk.Window, row: Gtk.Box, path: str) -> None:
    """Render the full gallery content to PNG at its full natural size.

    GTK allocates widgets to fit the on-screen window, which is capped by the
    monitor. Force-allocating the row at its natural size before snapshotting
    bypasses that, so a wide gallery is captured in full rather than clipped.

    No-ops silently on platforms where _snapshot_supported() returns False.
    """
    if not _snapshot_supported():
        return
    # Full natural size, unconstrained by the on-screen viewport.
    nat_width = row.measure(Gtk.Orientation.HORIZONTAL, UNCONSTRAINED)[1]
    nat_height = row.measure(Gtk.Orientation.VERTICAL, nat_width)[1]

    # Force the row and its subtree to lay out at the full size so the
    # snapshot captures everything, not just what fits on screen.
    row.allocate(nat_width, nat_height, NO_BASELINE, None)

    # do_snapshot draws content at (0, 0) — it doesn't apply the row's own margins
    # (that's normally done by the parent widget's snapshot machinery). To reproduce
    # the margin whitespace we shift the capture viewport instead: a
    # negative-origin rect tells the renderer to start capturing before the content,
    # so the margin space appears on all four sides of the output image.
    snapshot = Gtk.Snapshot.new()
    Gtk.Widget.do_snapshot(row, snapshot)
    node = snapshot.to_node()
    if node is None:
        return

    # Use the Cairo software renderer:
    # render_texture() via NGL/Vulkan produces corrupted output on some GPU/driver combinations
    # (observed on Intel Mesa).
    # Software rendering bypasses the GPU driver stack, so it is always consistent.
    from gi.repository import Gsk  # pylint: disable=import-outside-toplevel
    renderer = Gsk.CairoRenderer.new()
    renderer.realize(window.get_surface())
    rect = Graphene.Rect().init(
        -row.get_margin_start(), -row.get_margin_top(), nat_width, nat_height
    )
    try:
        texture = renderer.render_texture(node, rect)
    finally:
        renderer.unrealize()

    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    texture.save_to_png(path)


def _schedule_screenshot(window: Gtk.Window, row: Gtk.Box, path: str) -> None:
    """On the first rendered frame, take a screenshot then destroy the window.

    Called after present(), so the window is already realized and the frame
    clock is available. The actual paint hasn't happened yet (it runs on the
    next main-loop frame), so connecting to after-paint here catches it.
    """
    handler_id = None

    def _after_paint(frame_clock):
        frame_clock.disconnect(handler_id)
        _take_screenshot(window, row, path)
        window.destroy()

    handler_id = window.get_frame_clock().connect("after-paint", _after_paint)


def build_demo_widgets_for_screen(screen_name: str) -> List[Tuple[str, Gtk.Widget]]:
    """Run every factory registered for the screen, returning (label, widget) pairs."""
    pairs: List[Tuple[str, Gtk.Widget]] = []
    for entry in registry.entries_for(screen_name):
        result = entry.factory()
        widgets = result if isinstance(result, list) else [result]
        for widget in widgets:
            pairs.append((entry.label, widget))
    return pairs


class _FixedSizeLayout(Gtk.BinLayout):
    """A BinLayout that reports a fixed size instead of its child's natural size
    (the size the child would request given unlimited space).

    BinLayout already allocates the single child the box's whole area; we only
    override measure, so the child is laid out at exactly width x height — which
    reproduces a non-resizable window. (A ScrolledWindow would instead hand the
    child its natural size and scroll/clip the difference.)
    """

    def __init__(self, width: int, height: int):
        super().__init__()
        self._width = width
        self._height = height

    def do_measure(self, _widget, orientation, _for_size):  # pylint: disable=arguments-differ
        """Report the fixed size for `orientation` as both minimum and natural.

        Equal minimum and natural pins the box to that size whatever space is
        available; the trailing two values are the (absent) baselines.
        """
        size = (
            self._width if orientation == Gtk.Orientation.HORIZONTAL
            else self._height
        )
        return (size, size, NO_BASELINE, NO_BASELINE)


def fixed_size(child: Gtk.Widget, width: int, height: int) -> Gtk.Box:
    """Returns a box that locks `child` to an exact (width, height); see _FixedSizeLayout.
    """
    box = Gtk.Box()
    box.set_layout_manager(_FixedSizeLayout(width, height))
    box.set_hexpand(False)  # fixed size: never stretch to fill the gallery row
    box.set_vexpand(False)
    box.append(child)
    return box


def modal_content_size(windows: List[Gtk.Window]) -> Tuple[int, int]:
    """The single fixed size to show every variant of a modal screen at.

    The variants share one window in the app, so they're shown at one size: at
    least the window's default, never narrower than the widest variant's minimum
    width, and never shorter than the tallest variant needs at that width (so nothing is clipped).
    """
    width = 0
    for window in windows:
        content = window.get_child()
        default_width = window.get_default_size()[0]
        min_width = \
            content.measure(Gtk.Orientation.HORIZONTAL, UNCONSTRAINED)[0] if content else 0
        width = max(width, default_width, min_width)
    height = 0
    for window in windows:
        content = window.get_child()
        default_height = window.get_default_size()[1]
        natural_height = (
            content.measure(Gtk.Orientation.VERTICAL, width)[1] if content else 0
        )
        height = max(height, default_height, natural_height)
    return width, height


def embed_window(window: Gtk.Window, size: Tuple[int, int]) -> Gtk.Widget:
    """Lift a top-level window's content into an embeddable widget.

    A Gtk.Window can't be nested in another widget, so to show a modal/dialog
    inside the gallery we reparent its content into a bin sized to `size` and
    copy the window's CSS name and classes onto it, so window-scoped rules still
    match. Window styling that isn't app CSS (titlebar, compositor shadow) is
    not reproduced.
    """
    content = window.get_child()
    window.set_child(None)  # detach so the content can be shown in the gallery

    if content is not None:
        wrapper = fixed_size(content, *size)
    else:
        wrapper = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

    wrapper.set_name(window.get_name())
    for css_class in window.get_css_classes():
        wrapper.add_css_class(css_class)
    wrapper.set_halign(Gtk.Align.START)
    wrapper.set_valign(Gtk.Align.START)
    return wrapper


def _labelled_group(label: str, widget: Gtk.Widget) -> Gtk.Widget:
    """A caption above its widget — one cell of the gallery.

    Top-aligned so a short cell isn't stretched to the height of a taller one
    beside it.
    """
    group = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
    group.set_halign(Gtk.Align.START)
    group.set_valign(Gtk.Align.START)
    caption = Gtk.Label(label=label.upper(), xalign=0)
    caption.add_css_class("demo-label")
    caption.set_halign(Gtk.Align.START)
    group.append(caption)
    # The shadow lives on this scaffolding card, not the widget, so the widget's
    # own CSS stays untouched for evaluation.
    card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
    card.add_css_class("demo-bounds")
    card.append(widget)
    group.append(card)
    return group


def build_window(screen_name: str) -> DemoGallery:
    """Build (without presenting) the gallery window that shows the screen.

    Every entry — embeddable widget or reparented top-level — becomes a labelled
    cell laid out left to right at its fixed size, so states sit side by side
    with nothing floating or overlapping. Raises KeyError if no demo is
    registered for the screen.
    """
    labelled_widgets = build_demo_widgets_for_screen(screen_name)
    if not labelled_widgets:
        raise KeyError(f"No demo registered for screen {screen_name!r}")

    # Reparented modals share one fixed size so every variant matches (they share
    # one window in the app); embeddable widgets keep their own.
    modal_windows = [w for _, w in labelled_widgets if isinstance(w, Gtk.Window)]
    modal_size = modal_content_size(modal_windows) if modal_windows else None

    row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=_MARGIN)
    row.set_valign(Gtk.Align.START)
    row.set_margin_top(_MARGIN)
    row.set_margin_bottom(_MARGIN)
    row.set_margin_start(_MARGIN)
    row.set_margin_end(_MARGIN)
    for label, widget in labelled_widgets:
        if isinstance(widget, Gtk.Window):
            widget = embed_window(widget, modal_size)
        else:
            # framed_like_app already pinned the widget to the app size via
            # set_size_request; read that back — its width, then its
            # height-for-width — and lock the cell to it. Otherwise the
            # auto-sizing gallery would inflate to the widget's larger
            # unconstrained natural height (the login form's).
            natural_width = widget.measure(Gtk.Orientation.HORIZONTAL, UNCONSTRAINED)[1]
            height_for_width = widget.measure(
                Gtk.Orientation.VERTICAL, natural_width
            )[1]
            widget = fixed_size(widget, natural_width, height_for_width)
        row.append(_labelled_group(label, widget))

    # The window always auto-sizes to the content's exact natural size
    # (propagated by the ScrolledWindow, uncapped). If the user shrinks it below
    # that, the content scrolls rather than clipping.
    scrolled = Gtk.ScrolledWindow()
    scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
    scrolled.set_propagate_natural_width(True)
    scrolled.set_propagate_natural_height(True)
    scrolled.set_child(row)

    window = Gtk.Window()
    window.set_title(f"demo: {screen_name}")
    window.set_child(scrolled)
    return DemoGallery(window=window, row=row)


def show(
    application: Gtk.Application,
    screen_name: str,
    screenshot_path: Optional[str] = None,
) -> Gtk.Window:
    """Build the gallery window, attach it to the application and present it.

    If screenshot_path is given, save a PNG on the first painted frame and exit.
    """
    Gtk.Settings.get_default().props.gtk_application_prefer_dark_theme = True
    _load_demo_css()

    gallery = build_window(screen_name)
    application.add_window(gallery.window)
    gallery.window.present()
    if screenshot_path is not None:
        _schedule_screenshot(gallery.window, gallery.row, screenshot_path)
    return gallery.window
