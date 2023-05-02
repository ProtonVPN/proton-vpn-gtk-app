"""
Semver utils.

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
from packaging.version import Version


def from_pep440(pep440_version: str) -> str:
    """
    Converts a PEP440 version to a semver version.

    Disclaimers:
     - It assumes the PEP440 version contains the major, minor, micro triplet (e.g. 1.2.3).
     - Date-based releases are not supported (e.g. 2023.05).
     - Post release segments are not supported, since semver doesn't allow them.

    https://peps.python.org/pep-0440
    https://semver.org
    """
    ver = Version(pep440_version)

    # Even though PEP440 doesn't require it, our versions always contain
    # the major, minor, and micro triplet.
    result = f"{ver.major}.{ver.minor}.{ver.micro}"

    if ver.pre is not None:
        prerelease_mappings = {
            "a": "alpha",
            "b": "beta",
            "rc": "rc"
        }
        result += f"-{prerelease_mappings[ver.pre[0]]}.{ver.pre[1]}"

    if ver.dev is not None:
        result += f"-dev.{ver.dev}"

    if ver.local is not None:
        result += f"+{ver.local}"

    return result
