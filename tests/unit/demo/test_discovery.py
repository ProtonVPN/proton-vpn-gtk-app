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


Tests for demo screen discovery (importing the *_demo modules).
"""
from unittest.mock import patch

from proton.vpn.app.gtk.demo import discovery, registry


def test_load_demo_screens_is_idempotent():
    """importlib caches modules, so repeat calls must not re-register entries."""
    discovery.load_demo_screens()
    before = len(registry.all_demo_entries())

    discovery.load_demo_screens()

    assert len(registry.all_demo_entries()) == before


def test_load_demo_screens_survives_a_broken_module():
    """One demo module failing to import must not abort discovery of the rest."""
    with patch.object(
        discovery.importlib, "import_module", side_effect=ImportError("boom")
    ):
        discovery.load_demo_screens()  # must not raise
