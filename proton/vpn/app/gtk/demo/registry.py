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


Registry of demo screens.

A demo entry is a (screen_name, label, factory) triple. A factory returns
either a single Gtk.Widget or a list of widgets (the states/variants to show
under that label). The @register_demo decorator records entries at import
time; the launcher reads the registry to build the window(s) for a screen.
"""
from dataclasses import dataclass
from typing import Callable, List, Union

from proton.vpn.app.gtk import Gtk

DemoFactory = Callable[[], Union[Gtk.Widget, List[Gtk.Widget]]]


@dataclass(frozen=True)
class DemoEntry:
    """A single registered demo: a labelled group and the factory that builds it."""
    screen_name: str
    label: str
    factory: DemoFactory


_REGISTRY: List[DemoEntry] = []


def register_demo(screen_name: str, label: str) -> Callable[[DemoFactory], DemoFactory]:
    """Register a demo factory under a screen name and group label.

        @register_demo("bug-report", label="empty")
        def _empty():
            return BugReportDialog(...)

    The decorated function is returned unchanged; the decorator only records it.
    """
    def decorator(factory: DemoFactory) -> DemoFactory:
        _REGISTRY.append(DemoEntry(screen_name, label, factory))
        return factory

    return decorator


def all_demo_entries() -> List[DemoEntry]:
    """All registered entries, in registration order."""
    return list(_REGISTRY)


def all_demo_screen_names() -> List[str]:
    """Registered screen names, de-duplicated, in first-seen order."""
    ordered = {}
    for entry in _REGISTRY:
        ordered.setdefault(entry.screen_name, None)
    return list(ordered)


def entries_for(screen_name: str) -> List[DemoEntry]:
    """Entries registered for one screen, in registration order."""
    return [entry for entry in _REGISTRY if entry.screen_name == screen_name]
