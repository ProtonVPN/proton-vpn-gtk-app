"""
This module contains utility tools.

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
import re
from importlib.metadata import distributions
from typing import Callable
from gi.repository import Gtk

from proton.vpn import logging
from proton.vpn.app.gtk.utils.safe_signal_connect import safe_signal_connect

# See: https://docs.gtk.org/gtk4/migrating-3to4.html#set-a-proper-application-id  # pylint: disable=line-too-long # noqa: E501
APPLICATION_ID = "proton.vpn.app.gtk"

logger = logging.getLogger(__name__)


def log_proton_package_versions():
    """Logs the versions of all installed proton-* python packages."""
    seen = set()
    packages = []
    for dist in distributions():
        name = dist.metadata["Name"]
        if name and re.match(r"proton", name, re.IGNORECASE) and name not in seen:
            seen.add(name)
            packages.append(f"{name}=={dist.metadata['Version']}")
    logger.info("Proton python packages:\n" + "\n".join(sorted(packages)))


def connect_once(widget: Gtk.Widget, signal: str, callback: Callable) -> int:
    """Subscribe to *widget*'s *signal* once. The handler is disconnected
    after the signal fires for the first time, or after the callback's
    bound instance is collected — whichever comes first.

    Same callback restrictions as safe_signal_connect:
    bound method (held weakly) or pure free function (no closure
    captures); closure-capturing callables raise ``TypeError``."""
    return safe_signal_connect(widget, signal, callback, once=True)


__all__ = ["connect_once"]
