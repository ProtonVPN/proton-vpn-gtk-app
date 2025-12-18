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
from typing import Callable
from gi.repository import Gtk

# See: https://docs.gtk.org/gtk4/migrating-3to4.html#set-a-proper-application-id  # pylint: disable=line-too-long # noqa: E501
APPLICATION_ID = "proton.vpn.app.gtk"


def connect_once(widget: Gtk.Widget, signal: str, callback: Callable, *args):
    """Subscribes to the signal once."""
    context = {}

    def wrapper(*args, **kwargs):
        widget.disconnect(context["id"])
        callback(*args, **kwargs)

    context["id"] = widget.connect(signal, wrapper, *args)
    return context["id"]


__all__ = ["connect_once"]
