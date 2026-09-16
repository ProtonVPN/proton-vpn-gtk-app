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
import pytest

from proton.vpn.app.gtk.utils.change_server_cooldown import \
    ChangeServerCooldown, \
    format_countdown

SHORT_DELAY = 90
LONG_DELAY = 1200
ATTEMPT_LIMIT = 4


class FakeClock:
    """A clock that only moves when the test tells it to."""

    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now

    def advance(self, seconds):
        """Moves the clock forward."""
        self.now += seconds


def _client_config(attempt_limit=ATTEMPT_LIMIT):
    class ClientConfigStub:  # pylint: disable=too-few-public-methods
        """Only the fields the cooldown reads."""
        change_server_attempt_limit = attempt_limit
        change_server_short_delay_sec = SHORT_DELAY
        change_server_long_delay_sec = LONG_DELAY

    return ClientConfigStub()


def _cooldown(attempt_limit=ATTEMPT_LIMIT):
    clock = FakeClock()
    return ChangeServerCooldown(clock=clock), clock, _client_config(attempt_limit)


def test_cooldown_is_not_active_before_it_is_armed():
    cooldown, _, _ = _cooldown()

    assert cooldown.is_active is False


def test_the_remaining_time_decreases_as_time_passes():
    cooldown, clock, client_config = _cooldown()
    cooldown.arm(client_config)

    clock.advance(30)

    assert cooldown.remaining_seconds == SHORT_DELAY - 30


def test_the_cooldown_is_over_once_the_delay_has_elapsed():
    cooldown, clock, client_config = _cooldown()
    cooldown.arm(client_config)
    assert cooldown.is_active is True

    clock.advance(SHORT_DELAY)

    assert cooldown.is_active is False
    assert cooldown.remaining_seconds == 0


def test_the_remaining_time_never_goes_negative():
    cooldown, clock, client_config = _cooldown()
    cooldown.arm(client_config)

    clock.advance(SHORT_DELAY * 10)

    assert cooldown.remaining_seconds == 0


@pytest.mark.parametrize("attempt_limit", [1, 2, ATTEMPT_LIMIT])
def test_the_attempt_that_reaches_the_limit_uses_the_long_delay(attempt_limit):
    cooldown, clock, client_config = _cooldown(attempt_limit)

    for _ in range(attempt_limit - 1):
        cooldown.arm(client_config)
        assert cooldown.is_long is False
        assert cooldown.remaining_seconds == SHORT_DELAY
        clock.advance(SHORT_DELAY)

    cooldown.arm(client_config)

    assert cooldown.is_long is True
    assert cooldown.remaining_seconds == LONG_DELAY


def test_the_attempt_after_the_long_delay_uses_the_short_delay_again():
    cooldown, clock, client_config = _cooldown()
    for _ in range(ATTEMPT_LIMIT):
        cooldown.arm(client_config)
        clock.advance(cooldown.remaining_seconds)

    cooldown.arm(client_config)

    assert cooldown.is_long is False
    assert cooldown.remaining_seconds == SHORT_DELAY


def test_arming_the_cooldown_again_restarts_the_delay():
    cooldown, clock, client_config = _cooldown()
    cooldown.arm(client_config)
    clock.advance(SHORT_DELAY - 10)

    cooldown.arm(client_config)

    assert cooldown.remaining_seconds == SHORT_DELAY


@pytest.mark.parametrize("seconds, expected", [
    (0, "00:00"),
    (0.1, "00:01"),
    (1, "00:01"),
    (59, "00:59"),
    (59.1, "01:00"),
    (60, "01:00"),
    (90, "01:30"),
    (1200, "20:00"),
])
def test_the_countdown_is_formatted_as_minutes_and_seconds(seconds, expected):
    assert format_countdown(seconds) == expected
