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


Mock helpers for demo widget factories.
"""
from unittest.mock import MagicMock

from proton.vpn.connection.enum import KillSwitchSetting


def mock_controller(killswitch: KillSwitchSetting = KillSwitchSetting.OFF) -> MagicMock:
    """A shared Controller mock for demo screens to construct and render.

    `get_settings().killswitch` is read at render time by the login widget.
    """
    controller = MagicMock(name="Controller")
    controller.get_settings.return_value.killswitch = killswitch
    return controller


def mock_main_window() -> MagicMock:
    """A MainWindow mock."""
    return MagicMock(name="MainWindow")
