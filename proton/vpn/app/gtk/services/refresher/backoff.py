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
import random
from proton.vpn.core.session.credentials import VPNPubkeyCredentials


def generate_backoff_value(
    number_of_failed_refresh_attempts: int,
    backoff_in_seconds: int = 1,
    random_component: int = None
) -> int:
    """Generate and return a backoff value for when API calls fail,
    so it can retry again without DDoS'ing the API."""
    random_component = random_component or _generate_random_component()
    return backoff_in_seconds * 2 ** number_of_failed_refresh_attempts * random_component


def _generate_random_component() -> int:
    return 1 + VPNPubkeyCredentials.REFRESH_RANDOMNESS * (2 * random.random() - 1)  # nosec B311


__all__ = ["generate_backoff_value"]
