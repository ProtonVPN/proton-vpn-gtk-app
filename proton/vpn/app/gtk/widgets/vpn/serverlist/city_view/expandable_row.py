"""
Reusable expandable row with header and revealable content.

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

from typing import Callable, List, Tuple

from proton.vpn.app.gtk import Gtk

from proton.vpn.app.gtk.utils.safe_signal_connect import safe_signal_connect
from proton.vpn.app.gtk.widgets.vpn.serverlist.city_view.row_content import RowContent
from proton.vpn.app.gtk.widgets.vpn.serverlist.city_view.utils import get_children


class ExpandableRow(Gtk.Box):
    """Reusable expandable row with header and revealable content area."""

    def __init__(
        self,
        on_expand: Callable[[], None],
        on_collapse: Callable[[], None],
    ):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self._on_expand = on_expand
        self._on_collapse = on_collapse
        self._row_content = RowContent()
        self.append(self._row_content)
        self._revealer = Gtk.Revealer()
        self._container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self._container.set_spacing(5)
        self._container.set_margin_top(5)
        self._revealer.set_child(self._container)
        self.append(self._revealer)
        self._connected_signals: List[Tuple[int, Gtk.Widget]] = []
        self._revealer_collapse_signal_id = None
        safe_signal_connect(self, "unrealize", self._on_unrealize)

    @property
    def row_content(self) -> RowContent:
        """The row content (header area)."""
        return self._row_content

    @property
    def container(self) -> Gtk.Box:
        """The container for revealed content. Add child widgets here."""
        return self._container

    def get_children(self) -> list:
        """Returns the list of children in the content container."""
        return get_children(self._container)

    def remove_child(self, child: Gtk.Widget) -> None:
        """Removes a child from the content container."""
        self._container.remove(child)

    def connect_toggle(self) -> None:
        """Connects the toggle-children signal. Call after displaying the row content."""
        signal_id = safe_signal_connect(self._row_content, "toggle-children", self._on_toggle)
        self._connected_signals.append((signal_id, self._row_content))

    def _on_toggle(self, row_content: RowContent) -> None:
        self._set_revealed(row_content.expanded)

    def _set_revealed(self, expanded: bool) -> None:
        if expanded:
            if self._on_expand is not None:
                self._on_expand()
        else:
            self._schedule_collapse_on_reveal_complete()
        self._revealer.set_reveal_child(expanded)

    def set_expanded(self, expanded: bool) -> None:
        """Programmatically set expanded state and run expand/collapse logic."""
        self._row_content.expanded = expanded
        self._set_revealed(expanded)

    def _on_collapse_complete(self, *_args) -> None:
        self._revealer.disconnect(self._revealer_collapse_signal_id)
        self._connected_signals.remove((self._revealer_collapse_signal_id, self._revealer))
        if self._on_collapse is not None:
            self._on_collapse()

    def _schedule_collapse_on_reveal_complete(self) -> None:
        """Waits for the revealer to finish collapsing, then calls _on_collapse."""
        self._revealer_collapse_signal_id = safe_signal_connect(
            self._revealer,
            "notify::child-revealed",
            self._on_collapse_complete
        )
        self._connected_signals.append((self._revealer_collapse_signal_id, self._revealer))

    def _on_unrealize(self, _widget: Gtk.Widget) -> None:
        self.reset()
        self._on_expand = None
        self._on_collapse = None

    def reset(self, keep_children: bool = False) -> None:
        """Resets the row. Disconnects signals and optionally removes children."""
        for signal_id, widget in self._connected_signals:
            widget.disconnect(signal_id)
        self._connected_signals.clear()
        self._row_content.reset()
        if not keep_children and self._on_collapse is not None:
            self._on_collapse()
