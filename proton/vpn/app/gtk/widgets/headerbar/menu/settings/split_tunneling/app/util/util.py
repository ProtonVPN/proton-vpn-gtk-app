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
from typing import Union
import shutil
import html


from gi.repository import Gio
from proton.vpn.app.gtk.widgets.headerbar.menu.settings.split_tunneling.app.data_structures \
    import AppData
from proton.vpn.app.gtk.widgets.headerbar.menu.settings.split_tunneling.app.util.snap \
    import get_snap_app_data


def check_is_flatpak(executable: str) -> bool:
    """Check if executable is a flatpak.

    Args:
        executable (str):

    Returns:
        bool:
    """
    return "flatpak" in executable


def check_is_snap(dot_desktop_filepath: str) -> bool:
    """Check if the `dot_desktop_filepath` is in the snapd folder.

    Args:
        executable (str):

    Returns:
        bool:
    """
    return "snapd" in dot_desktop_filepath


def check_is_only_executable(executable: str) -> bool:
    """Check if executable is just a filename.

    Args:
        executable (str):

    Returns:
        bool:
    """
    # Some only store the executable name, while we need the full path
    return "/" not in executable and shutil.which(executable)


def _get_all_installed_apps() -> list[AppData]:
    """Gets a list of installed applications on the system.

    Returns:
        list[AppData]
    """
    app_list = []

    for app in Gio.AppInfo.get_all():
        native = True
        icon = None

        if not app.should_show():
            continue

        executable = app.get_executable()

        # If there is not executable then we can skip it
        if not executable:
            continue

        # This is the .desktop file
        dot_desktop_filepath = app.get_filename()

        if check_is_flatpak(executable):
            continue

        if check_is_snap(dot_desktop_filepath):
            native = False
            executable, icon = get_snap_app_data(dot_desktop_filepath)

            # If the app is missing executable then skip it as
            # something is wrong with this app
            if not executable:
                continue
        elif check_is_only_executable(executable):
            executable = shutil.which(executable)

        if not icon:
            received_icon: Union[Gio.ThemedIcon, Gio.FileIcon] = app.get_icon()
            if isinstance(received_icon, Gio.ThemedIcon):
                icon = received_icon.get_names()[0]

        app_list.append(AppData(
            name=html.escape(app.get_display_name()),
            executable=executable,
            icon_name=icon,
            native=native
        ))

    return app_list
