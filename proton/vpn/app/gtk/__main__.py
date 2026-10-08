"""
App entry point.


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

import sys

from gi.repository import Gio, GLib

from proton.vpn.app.gtk.app import App
from proton.vpn.app.gtk.controller import Controller
from proton.vpn.app.gtk.util import APPLICATION_ID
from proton.vpn.app.gtk.utils.exception_handler import ExceptionHandler
from proton.vpn.app.gtk.utils.executor import AsyncExecutor

# Timeouts, in milliseconds, for the two D-Bus calls used to hand over to an
# already-running instance.
NAME_HAS_OWNER_TIMEOUT_MS = 1000
ACTIVATE_TIMEOUT_MS = 5000


def activate_running_instance() -> bool:
    """Hands over to an already-running app instance, if there is one.

    Returns True if another instance was found and asked to present itself,
    meaning this process should exit without starting anything.

    Gtk.Application only discovers that it is redundant once run() registers it
    on the session bus. By that point Controller.get() has already started the
    asyncio executor and the Rust local agent's tokio runtime. run() then
    returns immediately, and interpreter finalization races those still-running
    threads: the tokio workers call into CPython while Py_Finalize() is freeing
    the interpreter, which segfaults.

    Checking for the well-known name first keeps a redundant instance from ever
    starting that machinery.

    Only the no-arguments case is short-circuited, so --version and
    --start-minimized keep going through Gtk.Application's own option handling.
    """
    if len(sys.argv) > 1:
        return False

    try:
        bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)

        is_running = bus.call_sync(
            "org.freedesktop.DBus",
            "/org/freedesktop/DBus",
            "org.freedesktop.DBus",
            "NameHasOwner",
            GLib.Variant("(s)", (APPLICATION_ID,)),
            GLib.VariantType("(b)"),
            Gio.DBusCallFlags.NONE,
            NAME_HAS_OWNER_TIMEOUT_MS,
            None,
        ).unpack()[0]

        if not is_running:
            return False

        bus.call_sync(
            APPLICATION_ID,
            "/" + APPLICATION_ID.replace(".", "/"),
            "org.gtk.Application",
            "Activate",
            GLib.Variant("(a{sv})", ({},)),
            None,
            Gio.DBusCallFlags.NONE,
            ACTIVATE_TIMEOUT_MS,
            None,
        )
        return True
    except GLib.Error:
        # If the probe fails for any reason, fall through to the normal startup
        # path and let Gtk.Application deal with it.
        return False


def main():
    """Runs the app."""
    if activate_running_instance():
        return

    with AsyncExecutor() as executor, ExceptionHandler() as exception_handler:
        controller = Controller.get(executor, exception_handler)
        sys.exit(App(controller).run(sys.argv))


if __name__ == "__main__":
    main()
