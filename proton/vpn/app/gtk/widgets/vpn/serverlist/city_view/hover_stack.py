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

from typing import List, Optional, Tuple

from gi.repository import GLib, GObject

from proton.vpn.app.gtk import Gtk
from proton.vpn.app.gtk.utils.safe_signal_connect import safe_signal_connect


class HoverStack(Gtk.Stack):
    """
    A Gtk.Stack that switches between two children based on hover/focus state.

    The two pages are:
      - "hover_child": shown on hover or keyboard focus (e.g. a connect button).
      - "leave_child": shown otherwise (e.g. feature icons).
    """

    def __init__(
        self,
        leave_child: Optional[Gtk.Widget] = None,
        hover_child: Optional[Gtk.Widget] = None,
        parent_for_hover: Optional[Gtk.Widget] = None,
    ):
        super().__init__()
        self.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self.set_transition_duration(70)
        self.set_focusable(True)

        self._is_hovered = False
        self._hover_parent = parent_for_hover or self
        self._motion_controller: Optional[Gtk.EventControllerMotion] = None
        self._child_focus_controller: Optional[Gtk.EventControllerFocus] = None
        self._connected_signals: List[Tuple[int, GObject.Object]] = []

        if leave_child is not None:
            self.set_leave_child(leave_child)
        if hover_child is not None:
            self.set_hover_child(hover_child)

    def do_focus(self, direction):  # pylint: disable=arguments-differ
        hover_child = self.get_hover_child()
        if hover_child:
            if hover_child.has_focus():
                # Already focused — let Tab leave the stack.
                return False
            self.show_hover_child()
            return hover_child.grab_focus()
        return Gtk.Stack.do_focus(self, direction)

    def set_leave_child(self, child: Gtk.Widget) -> None:
        """Replace the leave-page child."""
        existing = self.get_child_by_name("leave_child")
        if existing is not None:
            self.remove(existing)
        self.add_named(child, "leave_child")
        self.set_visible_child_name("leave_child")

    def set_hover_child(self, child: Gtk.Widget) -> None:
        """Replace the hover-page child."""
        self.clear_hover_child()
        self.add_named(child, "hover_child")
        self._setup_visibility_handlers()

    def get_leave_child(self) -> Optional[Gtk.Widget]:
        """Return the current leave-page child, or None."""
        return self.get_child_by_name("leave_child")

    def get_hover_child(self) -> Optional[Gtk.Widget]:
        """Return the current hover-page child, or None."""
        return self.get_child_by_name("hover_child")

    def clear_hover_child(self) -> None:
        """Remove the hover-page child and tear down visibility handlers."""
        child = self.get_hover_child()
        if child is not None:
            self._remove_visibility_handlers()
            self.remove(child)

    def clear_leave_child(self) -> None:
        """Remove the leave-page child."""
        child = self.get_child_by_name("leave_child")
        if child is not None:
            self.remove(child)

    def show_hover_child(self) -> None:
        """Switch to the hover-child page."""
        self.set_visible_child_name("hover_child")

    def show_leave_child(self) -> None:
        """Switch to the leave-child page."""
        self.set_visible_child_name("leave_child")

    def reset(self) -> None:
        """Clear both children, restoring the object to its post-constructor state."""
        self.clear_hover_child()
        self.clear_leave_child()

    def _setup_visibility_handlers(self) -> None:
        """Attach hover and focus controllers after a hover child has been set."""
        self._is_hovered = False

        self._motion_controller = Gtk.EventControllerMotion()
        signal_id = self._motion_controller.connect("enter", lambda *_: self._on_hover_enter())
        self._connected_signals.append((signal_id, self._motion_controller))
        signal_id = self._motion_controller.connect("leave", lambda *_: self._on_hover_leave())
        self._connected_signals.append((signal_id, self._motion_controller))
        self._hover_parent.add_controller(self._motion_controller)

        child = self.get_hover_child()
        if child is None:
            return
        self._child_focus_controller = Gtk.EventControllerFocus()
        signal_id = self._child_focus_controller.connect(
            "leave", lambda _: self._on_child_focus_leave()
        )
        self._connected_signals.append((signal_id, self._child_focus_controller))
        child.add_controller(self._child_focus_controller)

        child_gtype = type(child).__gtype__  # type: ignore[attr-defined]
        has_clicked = GObject.signal_lookup("clicked", child_gtype) != 0
        if has_clicked:
            signal_id = safe_signal_connect(child, "clicked", self._on_hover_child_clicked)
            self._connected_signals.append((signal_id, child))

    def _remove_visibility_handlers(self) -> None:
        """Remove all hover and focus controllers and disconnect signals."""
        self._is_hovered = False

        if self._motion_controller is not None:
            self._hover_parent.remove_controller(self._motion_controller)
            self._motion_controller = None

        child = self.get_hover_child()
        if child is not None and self._child_focus_controller is not None:
            child.remove_controller(self._child_focus_controller)
        self._child_focus_controller = None

        for signal_id, widget in self._connected_signals:
            widget.disconnect(signal_id)
        self._connected_signals.clear()

    def _on_hover_enter(self) -> None:
        self._is_hovered = True
        self.show_hover_child()

    def _on_hover_leave(self) -> None:
        self._is_hovered = False
        if not self._hover_child_has_focus():
            self.show_leave_child()

    def _on_child_focus_leave(self) -> None:
        if not self._is_hovered:
            self.show_leave_child()

    def _on_hover_child_clicked(self, _widget) -> None:
        def release_focus():
            # After clicking on the child widget, move the focus back to
            # the HoverStack itself so that hover_child is hidden again.
            self.grab_focus()
            if not self._is_hovered:
                self.show_leave_child()

        GLib.idle_add(release_focus)

    def _hover_child_has_focus(self) -> bool:
        child = self.get_hover_child()
        return child is not None and child.has_focus()
