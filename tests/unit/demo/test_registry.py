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


Tests for the demo registry: registration, lookup and ordering.
"""
from proton.vpn.app.gtk import Gtk
from proton.vpn.app.gtk.demo.registry import (
    DemoEntry,
    all_demo_screen_names,
    entries_for,
    register_demo,
)


def test_register_demo_returns_the_factory_unchanged(clean_registry):
    """The decorator only records the factory; it must return it untouched."""
    def factory():
        return Gtk.Label()

    assert register_demo("s", label="l")(factory) is factory


def test_register_demo_records_an_entry(clean_registry):
    def factory():
        return Gtk.Label()

    register_demo("s", label="l")(factory)

    assert entries_for("s") == [DemoEntry("s", "l", factory)]


def test_entries_for_unknown_screen_is_empty():
    assert entries_for("no-such-screen") == []


def test_entries_for_returns_registration_order(clean_registry):
    register_demo("s", label="a")(lambda: Gtk.Label())
    register_demo("s", label="b")(lambda: Gtk.Label())

    assert [entry.label for entry in entries_for("s")] == ["a", "b"]


def test_all_demo_screen_names_dedupes_in_first_seen_order(clean_registry):
    register_demo("first", label="x")(lambda: Gtk.Label())
    register_demo("second", label="y")(lambda: Gtk.Label())
    register_demo("first", label="z")(lambda: Gtk.Label())  # second registration

    names = all_demo_screen_names()

    # "first" appears once (deduped) and before "second" (first-seen order).
    assert [name for name in names if name in ("first", "second")] == ["first", "second"]
