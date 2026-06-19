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


Shared fixtures for the demo tests.
"""
import pytest

from proton.vpn.app.gtk.demo import registry


@pytest.fixture
def clean_registry():
    """Snapshot the demo registry and restore it afterwards.

    The registry is module-global, so a test that registers its own demos would
    otherwise leak them into every later test. This restores the exact contents
    that were present before the test ran.
    """
    saved = list(registry._REGISTRY)  # pylint: disable=protected-access
    try:
        yield
    finally:
        registry._REGISTRY[:] = saved  # pylint: disable=protected-access
