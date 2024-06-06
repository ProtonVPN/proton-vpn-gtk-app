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
from proton.vpn.app.gtk.services.refresher.backoff import generate_backoff_value


def test_generate_backoff_value_generates_expected_value():
    backoff_in_seconds = 5
    number_of_failed_refresh_attempts = 3
    random_component = 8

    expected_value = backoff_in_seconds * 2 ** number_of_failed_refresh_attempts * random_component
    generated_value = generate_backoff_value(
        number_of_failed_refresh_attempts=number_of_failed_refresh_attempts,
        backoff_in_seconds=backoff_in_seconds,
        random_component=random_component
    )

    assert expected_value == generated_value
