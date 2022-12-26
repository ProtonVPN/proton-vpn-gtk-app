"""
User session monitoring.
"""
from typing import Callable
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


class SessionMonitor:
    """
    After being enabled, it calls the callback set on the
    session_unlocked_callback attribute whenever the user session was unlocked.

    Attributes:
        session_unlocked_callback: callable that will be called when the user
        session is unlocked.
    """
    def __init__(self, bus: SystemBus = None, session_object_path: str = None):
        self._bus = bus
        self._session_object_path = session_object_path
        self._signal_receiver = None
        self.session_unlocked_callback: Callable = None

    def enable(self):
        """Enables user session monitoring."""
        if not callable(self.session_unlocked_callback):
            raise RuntimeError("Callback was not set")

        if not self._bus:
            self._bus = SystemBus()

        if not self._session_object_path:
            self._setup()

        self._signal_receiver = self._bus.add_signal_receiver(
            handler_function=self.session_unlocked_callback,
            signal_name=UNLOCK_SIGNAL,
            dbus_interface=SESSION_INTERFACE,
            bus_name=BUS_NAME,
            path=self._session_object_path,
        )

    def disable(self):
        """Disables user session monitoring"""
        if self._signal_receiver:
            self._signal_receiver.remove()
            self._signal_receiver = None

    @property
    def is_session_unlocked(self):
        """Returns True if the user session is unlocked or False otherwise."""
        return True

    def _setup(self):
        seat_auto_proxy = self._bus.get_object(
            BUS_NAME,
            SEAT_AUTO_PATH
        )

        seat_auto_properties_proxy = dbus.Interface(
            seat_auto_proxy,
            PROPERTIES_INTERFACE
        )

        # There should always be session for a seat. If there is no seat then
        # it means that the user is not directly controlling the machine,
        # but rather controlloing it via ssh or some other indirect
        # type of control.
        seat_properties = seat_auto_properties_proxy.GetAll(SEAT_INTERFACE)
        active_sessions = seat_properties.get("ActiveSession", [])

        if not active_sessions:
            raise RuntimeError("There are no active sessions for this seat")

        _session_id, self._session_object_path = active_sessions

    def set_signal_receiver(self, new_object: object):
        """Sets signal receiver.
        This is mainly used for testing purposes.
        """
        self._signal_receiver = new_object
