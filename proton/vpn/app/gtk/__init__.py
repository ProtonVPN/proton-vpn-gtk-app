"""
This module includes the Proton VPN GTK application for Linux.


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
from importlib.metadata import version, PackageNotFoundError
import gi

try:
    __version__ = version("proton-vpn-gtk-app")
except PackageNotFoundError:
    __version__ = "development"

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk  # pylint: disable=C0413 # noqa: E402

from proton.vpn import logging  # pylint: disable=C0413 # noqa: E402


logging.config(filename="vpn-app")

__all__ = [Gtk]
