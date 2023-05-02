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

from proton.vpn.app.gtk.utils import semver


@pytest.mark.parametrize("pep440_version, expected_semver_version", [
    ("1.2.3", "1.2.3"),
    ("1.2.3a4", "1.2.3-alpha.4"),
    ("1.2.3b4", "1.2.3-beta.4"),
    ("1.2.3rc4", "1.2.3-rc.4"),
    ("1.2.3a4.dev5+abc", "1.2.3-alpha.4-dev.5+abc")
])
def test_from_pep440(pep440_version, expected_semver_version):
    result = semver.from_pep440(pep440_version)
    assert result == expected_semver_version
