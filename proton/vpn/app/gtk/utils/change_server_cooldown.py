"""
This module defines the cooldown applied to the "Change server" action.


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
import math
import time
from typing import Callable

from proton.vpn.session.session import ClientConfig


def format_countdown(seconds: float) -> str:
    """Formats a number of seconds as MM:SS.

    Seconds are rounded up so that the countdown only shows 00:00 once the
    cooldown is actually over.
    """
    minutes, seconds = divmod(math.ceil(seconds), 60)
    return f"{minutes:02d}:{seconds:02d}"


class ChangeServerCooldown:
    """
    How long the user has to wait before changing server again.

    Each server change starts a short cooldown, until the attempt limit is
    reached. That attempt starts a long cooldown instead and resets the
    counter, so the cooldown after it is short again. All the durations and
    the limit come from the client configuration.
    """

    def __init__(self, clock: Callable[[], float] = time.monotonic):
        self._clock = clock
        self._attempts = 0
        self._deadline = 0.0
        self._is_long = False

    def arm(self, client_config: ClientConfig):
        """
        Starts a new cooldown.

        :param client_config: source of the attempt limit and of both delays.
        """
        self._attempts += 1
        self._is_long = self._attempts >= client_config.change_server_attempt_limit
        if self._is_long:
            # Resetting attempts once the long cooldown is triggered
            self._attempts = 0

        delay = client_config.change_server_long_delay_sec if self._is_long \
            else client_config.change_server_short_delay_sec
        self._deadline = self._clock() + delay

    @property
    def remaining_seconds(self) -> float:
        """Returns how long is left of the current cooldown, 0 if it is over."""
        return max(0.0, self._deadline - self._clock())

    @property
    def is_active(self) -> bool:
        """Returns whether a cooldown is currently running."""
        return self.remaining_seconds > 0

    @property
    def is_long(self) -> bool:
        """Returns whether the current cooldown is the long one."""
        return self._is_long
