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


Anti-drift tests for demo mode.

These run every registered demo factory against the current widget code (with
the demo mocks) and build each screen's window. They check that that every demo
still *runs*.
"""
import pytest

from proton.vpn.app.gtk import Gtk
from proton.vpn.app.gtk.demo import discovery, registry, launcher
# process_gtk_events is itself decorated with raise_main_loop_exceptions, so
# calling it re-raises any exception GLib swallowed in a loop callback.
from tests.unit.testing_utils import process_gtk_events

# Run the @register_demo decorators once, at collection time, so the
# parametrize lists below are populated.
discovery.load_demo_screens()

ENTRIES = registry.all_demo_entries()
SCREENS = registry.all_demo_screen_names()


@pytest.mark.parametrize(
    "entry", ENTRIES, ids=[f"{e.screen_name}:{e.label}" for e in ENTRIES]
)
def test_demo_factory_runs(entry):
    """Every factory constructs against the current widget code without error."""
    result = entry.factory()
    widgets = result if isinstance(result, list) else [result]
    assert widgets, f"{entry.screen_name}:{entry.label} produced no widgets"
    assert all(isinstance(widget, Gtk.Widget) for widget in widgets)
    process_gtk_events()


@pytest.mark.parametrize("screen_name", SCREENS)
def test_demo_screen_builds_window(screen_name):
    """Every screen builds its gallery window without error."""
    gallery = launcher.build_window(screen_name)
    assert isinstance(gallery.window, Gtk.Window)
    process_gtk_events()
