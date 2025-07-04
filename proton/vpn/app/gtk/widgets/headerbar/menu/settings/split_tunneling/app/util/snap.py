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


def get_snap_app_data(snap_app_dot_desktop_file: str) -> tuple[Optional[str], Optional[str]]:
    """Returns the executable and icon that are extracted from a `.desktop` for for a given
    snap app.

    Args:
        snap_app_dot_desktop_file (str): The `.desktop` filepath for a given snap app

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
    config.read(snap_app_dot_desktop_file)

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
