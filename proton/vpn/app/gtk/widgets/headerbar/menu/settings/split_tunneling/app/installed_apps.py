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
from __future__ import annotations
from typing import Optional, Union
import html
import re
import shutil

from gi.repository import Gio
from proton.vpn.app.gtk.widgets.headerbar.menu.settings.split_tunneling.app.data_structures \
    import AppData
from proton.vpn.app.gtk.util import APPLICATION_ID
from proton.vpn import logging

logger = logging.getLogger(__name__)

PROTON_VPN_APP_ID_DOT_DESKTOP = f"{APPLICATION_ID}.desktop"


# This regex is used to extract the executable from a flatpak app's `.desktop` file.
# It matches the pattern of a flatpak app's executable.
# The regex captures the app start command.
# Example:
#   `/usr/bin/flatpak run --branch=stable --arch=x86_64 --command=mock-app @@ %u @@`
# The captured group will be:
#   `/usr/bin/flatpak run --branch=stable --arch=x86_64 --command=mock-app`
# Some flatpak apps might not have the `@@ ... @@`.
FLATPAK_PATTERN = re.compile(r"^(.+?)(?:\s*@@|$)")


class DesktopFileParsingError(Exception):
    """Error while parsing desktop file."""


def _check_is_flatpak(app: Gio.AppInfo) -> bool:
    """Check if executable is a flatpak. """
    command_line = app.get_commandline()
    return command_line.startswith("flatpak") or command_line.startswith("/usr/bin/flatpak")


def _get_flatpak_executable(app: Gio.AppInfo) -> str:
    """
    Returns the flatpak command line string trimming file forwarding
    specified with @@ ... @@. See FLATPAK_PATTERN regex.
    More info:
    https://unix.stackexchange.com/questions/797031/what-does-u-and-mean-in-the-a-desktop-entry
    https://docs.flatpak.org/en/latest/flatpak-command-reference.html
    """
    command_line = app.get_commandline()
    result = FLATPAK_PATTERN.search(command_line)

    if not result:
        raise DesktopFileParsingError(
            "Could not parse flatpack executable string from: {command_line}"
        )

    return result.group(1).rstrip()


def _check_is_snap(app: Gio.AppInfo) -> bool:
    """Checks if the command line string runs a snap app."""
    command_line = app.get_commandline()
    return command_line.startswith("/snap/bin/")


def _get_snap_executable(app: Gio.AppInfo) -> str:
    """
    Transforms "/snap/bin/<app-name> ..." to "/snap/<app-name>/".
    Returns the transformed string or None if the exe string can't be parsed.
    """
    command_line = app.get_commandline()
    re_result = re.search(r"/snap/bin/([\w\-.]*).", command_line)

    if not re_result:
        raise DesktopFileParsingError(f"Could not parse snap app ID from: {command_line}")

    # From `/snap/bin/<app-name>` will return `<app-name>`
    app_name = re_result.group(1)

    return f"/snap/{app_name}/"


def _check_is_command(command_line: str) -> bool:
    """
    Checks if command line contains a command (i.e. argv[0] is not an absolute path).
    :returns: True if it's a command, and False otherwise.
    """
    command, *_ = command_line.split()
    return "/" not in command and shutil.which(command)


def _get_native_app_executable(app: Gio.AppInfo):
    """Gets the full exe path for a command (+args)."""
    executable = app.get_executable()

    if _check_is_command(executable):
        executable = shutil.which(executable)

    if not executable:
        raise DesktopFileParsingError(
            "Could not get path from command: {command}"
        )

    return executable


def get_app_icon(app: Gio.AppInfo) -> Optional[str]:
    """Returns either the name of a themed icon or the full path to the icon."""
    icon = None

    received_icon: Union[Gio.ThemedIcon, Gio.FileIcon] = app.get_icon()
    if isinstance(received_icon, Gio.ThemedIcon):
        icon = received_icon.get_names()[0]
    elif isinstance(received_icon, Gio.FileIcon):
        icon = received_icon.get_file().get_path()

    return icon


def get_app_executable(app: Gio.AppInfo) -> str:
    """
    Returns the executable to split tunnel, transformed if necessary.
    """

    if _check_is_flatpak(app):
        executable = _get_flatpak_executable(app)
    elif _check_is_snap(app):
        executable = _get_snap_executable(app)
    else:
        executable = _get_native_app_executable(app)

    return executable


def get_all_installed_apps() -> list[AppData]:
    """Gets a list of installed applications on the system."""
    app_list = []

    for app in Gio.AppInfo.get_all():
        if not app.should_show():
            continue

        # Let's not split tunnel the vpn client itself,
        # otherwise it's not possible to connect to the VPN.
        if app.get_id() == PROTON_VPN_APP_ID_DOT_DESKTOP:
            continue

        try:
            executable = get_app_executable(app)
        except DesktopFileParsingError:
            logger.warning(
                "Could not get app executable for %s", app.get_filename(),
                exc_info=True
            )
            continue

        icon = get_app_icon(app)

        app_list.append(AppData(
            name=html.escape(app.get_display_name()),
            executable=executable,
            icon_name=icon
        ))

    return sorted(app_list, key=lambda app: app.name)
