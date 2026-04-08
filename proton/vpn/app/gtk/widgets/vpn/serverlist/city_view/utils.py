"""
Utility functions for server list widgets.


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
import itertools
from typing import Any, Callable, List, Type, TypeVar

from gi.repository import GLib

from proton.vpn.app.gtk import Gtk
from proton.vpn.app.gtk.controller import Controller
from proton.vpn.session.servers import ServerList

GtkWidget = TypeVar("GtkWidget", bound=Gtk.Widget)


def make_connect_callback(
    controller: Controller, servers: list, user_tier: int
) -> Callable[[], None]:
    """Returns a callback that connects to the fastest available server in the given list."""
    def on_connect():
        fastest = ServerList.get_fastest_server(
            ServerList.get_available_servers(servers=servers, user_tier=user_tier)
        )
        future = controller.connect_to_server(fastest.name)
        future.add_done_callback(lambda f: GLib.idle_add(f.result))
    return on_connect


def sync_rows_with_model_items(
    model_items: List[Any],
    existing_rows: List[GtkWidget],
    container: Gtk.Box,
    row_factory: Type[GtkWidget],
    display_func: Callable[[GtkWidget, Any], None]
):
    """Synchronizes a list of row widgets with model items using zip_longest.

    This utility function handles the common pattern of:
    - Creating new rows when there are more model items than rows
    - Removing rows when there are more rows than model items
    - Updating existing rows with their corresponding model items

    Row widgets should connect their reset() method to the "unrealize" signal
    for automatic cleanup when removed.

    Args:
        model_items: List of model objects to display
        existing_rows: List of existing row widgets
        container: Container widget to add/remove rows from
        row_factory: Callable that creates a new row widget (no arguments)
        display_func: Callable(row, model_item, ...) that updates a row with a model item
    """
    for model_item, row in itertools.zip_longest(model_items, existing_rows):
        if row is None:
            # More model items than rows - create new row
            row = row_factory()
            container.append(row)

        if model_item is None:
            # More rows than model items - remove row
            # Reset will be called automatically via unrealize signal
            container.remove(row)
        else:
            # Update existing row with model item
            display_func(row, model_item)


def get_children(widget: Gtk.Widget) -> List[Gtk.Widget]:
    """Returns the children of a widget."""
    children = []
    child = widget.get_first_child()
    while child:
        children.append(child)
        child = child.get_next_sibling()
    return children
