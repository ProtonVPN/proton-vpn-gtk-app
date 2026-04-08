"""
Login session service — wraps logind dbus interaction.


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
from typing import Any, Callable, Optional

import dbus
from dbus import SystemBus
from dbus.mainloop.glib import DBusGMainLoop

DBusGMainLoop(set_as_default=True)

BUS_NAME = "org.freedesktop.login1"
SEAT_AUTO_PATH = "/org/freedesktop/login1/seat/auto"
SESSION_INTERFACE = "org.freedesktop.login1.Session"
SEAT_INTERFACE = "org.freedesktop.login1.Seat"
PROPERTIES_INTERFACE = "org.freedesktop.DBus.Properties"
UNLOCK_SIGNAL = "Unlock"


class LoginSessionService:
    """
    Provides access to the current login session state via logind over dbus.

    Raises DBusUnavailableError when logind is inaccessible (e.g. under strict
    snap confinement with AppArmor blocking dbus access).
    """

    class DBusUnavailableError(Exception):
        """Raised when logind is inaccessible over dbus."""

    def __init__(
        self,
        bus: SystemBus = None,
        session_object_path: Optional[str] = None,
        dbus_interface: Optional[Callable[[Any, str], Any]] = None
    ):
        self._bus = bus or SystemBus()
        self._session_object_path = session_object_path
        self._dbus_interface = dbus_interface or dbus.Interface

    def add_session_unlocked_signal_receiver(self, handler: Callable) -> object:
        """
        Registers a handler to be called when the session is unlocked.
        Returns a signal receiver object that can be used to remove the handler.
        Raises DBusUnavailableError if logind is inaccessible.
        """
        try:
            if not self._session_object_path:
                self._setup()
        except dbus.exceptions.DBusException as exc:
            raise LoginSessionService.DBusUnavailableError() from exc

        return self._bus.add_signal_receiver(
            handler_function=handler,
            signal_name=UNLOCK_SIGNAL,
            dbus_interface=SESSION_INTERFACE,
            bus_name=BUS_NAME,
            path=self._session_object_path,
        )

    @property
    def is_session_unlocked(self) -> bool:
        """
        Returns True if the session is unlocked, False if locked.
        Raises DBusUnavailableError if logind is inaccessible.
        """
        try:
            if not self._session_object_path:
                self._setup()
            active_session = self._bus.get_object(BUS_NAME, self._session_object_path)
            active_session_properties = self._dbus_interface(active_session, PROPERTIES_INTERFACE)
            return not bool(active_session_properties.Get(SESSION_INTERFACE, "LockedHint"))
        except dbus.exceptions.DBusException as exc:
            raise LoginSessionService.DBusUnavailableError() from exc

    def _setup(self):
        seat_auto_proxy = self._bus.get_object(BUS_NAME, SEAT_AUTO_PATH)
        seat_auto_properties_proxy = self._dbus_interface(seat_auto_proxy, PROPERTIES_INTERFACE)

        seat_properties = seat_auto_properties_proxy.GetAll(SEAT_INTERFACE)
        active_sessions = seat_properties.get("ActiveSession", [])

        if not active_sessions:
            raise RuntimeError("There are no active sessions for this seat")

        _session_id, self._session_object_path = active_sessions
