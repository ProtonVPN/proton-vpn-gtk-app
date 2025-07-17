"""
Copyright (c) 2023 Proton AG

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
from typing import Callable

from proton.vpn import logging

from proton.vpn.core.settings import Settings

logger = logging.getLogger(__name__)


class SettingsWatchers:
    """
    A class to manage watchers for settings changes.
    It allows adding, removing, and notifying watchers when settings change.
    Each watcher is a callable that takes the updated settings as an argument.
    """
    def __init__(self):
        self.watchers = []

    def add(self, watcher: Callable[[Settings], None]):
        """Adds a new watcher to the list."""
        self.watchers.append(watcher)

    def remove(self, watcher: Callable[[Settings], None]):
        """Removes a watcher from the list."""
        if watcher in self.watchers:
            self.watchers.remove(watcher)

    def notify(self, settings: Settings):
        """Notifies all watchers with the new settings."""
        for watcher in self.watchers:
            watcher(settings)

    def clear(self):
        """Clears all watchers."""
        self.watchers.clear()
