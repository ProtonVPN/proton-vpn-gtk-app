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
"""
from __future__ import annotations

from typing import Callable, List, Optional, Tuple

from gi.repository import GLib, GObject

from proton.vpn.app.gtk import Gtk


class HoverBox(Gtk.Box):
    """
    A box that shows its content (opacity) only on hover (on a parent widget or itself)
    or on focus (on its child widget).
    Optional callbacks on_show/on_hide (e.g. hide another widget).
    """

    def __init__(
        self,
        on_show: Optional[Callable[[], None]] = None,
        on_hide: Optional[Callable[[], None]] = None,
        parent_for_hover: Optional[Gtk.Widget] = None,
    ):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL)
        self.add_css_class("hover-box")
        self._set_transparent(True)  # Hide content by default
        self._on_show = on_show
        self._on_hide = on_hide
        self._parent_for_hover = parent_for_hover or self
        self._is_hovered = False
        self._motion_controller = None
        self._child_focus_controller = None
        self._connected_signals: List[Tuple[int, Gtk.Widget]] = []

        self.set_focusable(True)

    def remove_child(self) -> None:
        """Remove the current child and tear down visibility handlers."""
        existing = self.get_child()
        if existing is not None:
            self._remove_visibility_handlers()
            self.remove(existing)

    def set_child(self, child: Optional[Gtk.Widget]) -> None:
        """Set the single child of the hover box (e.g. connect button or upgrade link)."""
        self.remove_child()
        if child is not None:
            self.append(child)
            self._set_transparent(True)  # Hide content by default
            self._setup_visibility_handlers()

    def get_child(self) -> Optional[Gtk.Widget]:
        """Return the single child of the hover box, or None."""
        return self.get_first_child()

    def is_content_visible(self) -> bool:
        """Return True if the child is shown (hover box does not have the transparent class)."""
        child = self.get_child()
        return child and child.get_visible() and "transparent" not in self.get_css_classes()

    def on_parent_hover_enter(self) -> None:
        """Called when the pointer enters the parent (e.g. header row)."""
        self._is_hovered = True
        self._show_content()

    def on_parent_hover_leave(self) -> None:
        """Called when the pointer leaves the parent. Hides only if focus is not on box or child."""
        self._is_hovered = False
        if not self._child_has_focus():
            self._hide_content()

    def on_child_focus_enter(self) -> None:
        """Called when focus enters the child. Shows content if the parent is hovered."""
        self._show_content()

    def on_child_focus_leave(self) -> None:
        """Called when focus leaves the child. Hides content if the parent is not hovered."""
        if not self._is_hovered:
            self._hide_content()

    def _child_has_focus(self) -> bool:
        child = self.get_child()
        return child is not None and child.has_focus()

    def _set_transparent(self, transparent: bool) -> None:
        if transparent:
            self.add_css_class("transparent")
        else:
            self.remove_css_class("transparent")

    def _show_content(self) -> None:
        if self._on_show:
            self._on_show()
        self._set_transparent(False)

    def _hide_content(self) -> None:
        self._set_transparent(True)
        if self._on_hide:
            self._on_hide()

    def _setup_visibility_handlers(self) -> None:
        """Attach hover/focus logic: motion on parent, focus on child only."""
        self._is_hovered = False
        self._motion_controller = Gtk.EventControllerMotion()
        self._motion_controller.connect("enter", lambda _c, _x, _y: self.on_parent_hover_enter())
        self._motion_controller.connect("leave", lambda _c: self.on_parent_hover_leave())
        self._parent_for_hover.add_controller(self._motion_controller)

        child = self.get_child()
        self._child_focus_controller = Gtk.EventControllerFocus()
        self._child_focus_controller.connect("enter", lambda _c: self.on_child_focus_enter())
        self._child_focus_controller.connect("leave", lambda _c: self.on_child_focus_leave())
        child.add_controller(self._child_focus_controller)

        if GObject.signal_lookup("clicked", type(child).__gtype__) != 0:
            signal_id = child.connect("clicked", self._on_child_clicked)
            self._connected_signals.append((signal_id, child))

    def _on_child_clicked(self, _widget: Gtk.Widget) -> None:
        """Clear focus from the child widget so that it's hidden again after clicking on it."""
        def release_focus():
            # Moving the focus from the child widget to the hover box itself causes the
            # child widget to be hidden again.
            self.grab_focus()

        GLib.idle_add(release_focus)

    def _remove_visibility_handlers(self) -> None:
        """Remove all hover and focus controllers."""
        self._is_hovered = False
        if self._motion_controller is not None:
            self._parent_for_hover.remove_controller(self._motion_controller)
        self._motion_controller = None

        for signal_id, widget in self._connected_signals:
            widget.disconnect(signal_id)
        self._connected_signals.clear()

        child = self.get_child()
        if child is not None and self._child_focus_controller is not None:
            child.remove_controller(self._child_focus_controller)
        self._child_focus_controller = None
