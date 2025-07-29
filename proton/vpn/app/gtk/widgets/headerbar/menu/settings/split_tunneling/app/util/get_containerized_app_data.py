"""
Copyright (c) 2025 Proton AG

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
from typing import Optional
import re
import configparser

# This regex is used to extract the executable from a flatpak app's `.desktop` file.
# It matches the pattern of a flatpak app's executable.
# The regex captures the app start command.
# Example:
#   `/usr/bin/flatpak run --branch=stable --arch=x86_64 --command=mock-app @@ %u @@`
# The captured group will be:
#   `/usr/bin/flatpak run --branch=stable --arch=x86_64 --command=mock-app`
# Some flatpak apps might not have the `@@ ... @@`.
FLATPAK_PATTERN = re.compile(r"^(.+?)(?:\s*@@|$)")


def get_snap_app_data(app_dot_desktop_file: str) -> tuple[Optional[str], Optional[str]]:
    """Returns the executable and icon that are extracted from a `.desktop` for for a given
    snap app.

    Args:
        app_dot_desktop_file (str): The `.desktop` filepath for a given snap app

    Returns:
        tuple[Optional[str], Optional[str]]: Returns the data for the given app.
            First argument is the executable and the second one is the icon filepath.
            If first argument is not found then both return False.
    """
    executable = None
    icon_name = None

    config = configparser.ConfigParser(
        interpolation=configparser.ExtendedInterpolation()
    )
    config.read(app_dot_desktop_file)

    # If an app has no executable then we just return as it's not worth
    # to continue, something is wrong
    executable_string = config.get("Desktop Entry", "Exec")
    if executable_string is None:
        return executable, icon_name

    # .search() returns either None or Match
    re_result = re.search(r"/snap/bin/([\w\-.]*).", executable_string)

    if not re_result:
        return executable, icon_name

    # From `/snap/bin/<app-name>` will return `<app-name>`
    re_result_bin = re_result.group(1)
    if not re_result_bin:
        return executable, icon_name

    executable = f"/snap/{re_result_bin}/"

    # Some apps might have missing icons, so it should be ok return None
    icon_name = config.get("Desktop Entry", "Icon", fallback=None)

    return executable, icon_name


def get_flatpak_executable(app_dot_desktop_file: str) -> Optional[str]:
    """Get the executable from a snap app's `.desktop` file.

    Args:
        app_dot_desktop_file (str): The `.desktop` filepath for a given snap app

    Returns:
        Optional[str]: Returns the executable path or None if not found.
    """
    config = configparser.ConfigParser(
        interpolation=configparser.ExtendedInterpolation()
    )
    config.read(app_dot_desktop_file)
    executable_string = config.get("Desktop Entry", "Exec")
    result = FLATPAK_PATTERN.search(executable_string)

    return result.group(1).rstrip() if result else None
