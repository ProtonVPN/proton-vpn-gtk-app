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
from typing import Any, Callable, List, Type, TypeVar, Union

from gi.repository import GLib

from proton.vpn.app.gtk import Gtk
from proton.vpn.app.gtk.controller import Controller
from proton.vpn.session.servers import (
    Country, Location, LogicalServer, SecureCoreGroup, ServerList, TierEnum
)

GtkWidget = TypeVar("GtkWidget", bound=Gtk.Widget)

FREE_RESCOPE_FLAG = "FreeRescope"


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


ServerListRow = Union[Country, Location, SecureCoreGroup, LogicalServer]


def upgrade_required_when_row_not_free(
    user_tier: TierEnum,
    row_is_free: bool
) -> bool:
    """Current behavior: upgrade required only when the row itself isn't free.
    Applies uniformly to any row — location, secure-core group, individual
    server, or country."""
    return user_tier == TierEnum.FREE and not row_is_free


def upgrade_required_unless_free_country_row(user_tier: TierEnum, row: ServerListRow) -> bool:
    """New behavior: only country rows are directly connectable for free-tier
    users. Every location, secure-core group, or individual server requires
    upgrade regardless of whether it's free — country rows are the sole
    exception and keep using the standard per-row-free formula."""
    if isinstance(row, Country):
        return upgrade_required_when_row_not_free(user_tier, row.free)
    return user_tier == TierEnum.FREE


def upgrade_required_for_row(
    controller: Controller,
    user_tier: TierEnum,
    row: ServerListRow
) -> bool:
    """Decides whether a server-list row requires upgrade for the given user
    tier, picking the behavior based on the FreeRescope feature flag."""
    if controller.feature_flags.get(FREE_RESCOPE_FLAG):
        return upgrade_required_unless_free_country_row(user_tier, row)
    return upgrade_required_when_row_not_free(user_tier, row.free)


def sync_rows_with_model_items(
    model_items: List[Any],
    rows: List[GtkWidget],
    container: Gtk.Box,
    row_factory: Type[GtkWidget],
    display_func: Callable[[GtkWidget, Any], None]
):
    """Synchronizes a list of row widgets with model items.

    This utility function handles the common pattern of:
    - Creating new rows when there are more model items than rows
    - Removing rows when there are more rows than model items
    - Updating existing rows with their corresponding model items

    ``rows`` is the source of truth and is mutated in place.
    Row widgets should connect their reset() method to the "unrealize"
    signal for automatic cleanup when removed.

    Args:
        model_items: List of model objects to display
        rows: Mutable list of row widgets owned by the caller
        container: Container widget to add/remove rows from
        row_factory: Callable that creates a new row widget (no arguments)
        display_func: Callable(row, model_item) that updates a row with a model item
    """
    for i, model_item in enumerate(model_items):
        if i >= len(rows):
            row = row_factory()
            rows.append(row)
            container.append(row)
        display_func(rows[i], model_item)

    while len(rows) > len(model_items):
        row = rows.pop()
        container.remove(row)


def get_children(widget: Gtk.Widget) -> List[Gtk.Widget]:
    """Returns the children of a widget."""
    children = []
    child = widget.get_first_child()
    while child:
        children.append(child)
        child = child.get_next_sibling()
    return children
