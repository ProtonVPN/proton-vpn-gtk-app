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


from gi.repository import Gio
from proton.vpn.app.gtk.widgets.headerbar.menu.settings.split_tunneling.app.data_structures \
    import AppData


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

        # Some only store the executable name, while we need the full path
        if "/" not in executable and shutil.which(executable):
            executable = shutil.which(executable)
        elif "flatpak" in executable:
            native = False

        received_icon: Union[Gio.ThemedIcon, Gio.FileIcon] = app.get_icon()
        if isinstance(received_icon, Gio.ThemedIcon):
            icon = received_icon.get_names()[0]

        app_list.append(AppData(
            name=app.get_display_name(),
            executable=executable,
            icon_name=icon,
            native=native
        ))

    return app_list
