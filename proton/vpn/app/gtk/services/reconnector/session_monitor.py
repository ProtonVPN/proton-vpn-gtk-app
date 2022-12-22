"""
User session monitoring.
"""
from typing import Callable
import dbus
from dbus import SystemBus
from dbus.mainloop.glib import DBusGMainLoop
DBusGMainLoop(set_as_default=True)


class SessionMonitor:
    """
    After being enabled, it calls the callback set on the
    session_unlocked_callback attribute whenever the user session was unlocked.

    Attributes:
        session_unlocked_callback: callable that will be called when the user
        session is unlocked.
    """
    def __init__(self, bus: SystemBus = None):
        self._bus = bus
        self._session_object_path = None
        self._signal_receiver = None
        self.session_unlocked_callback: Callable = None

    def enable(self):
        """Enables user session monitoring."""
        if not self._bus:
            self._bus = SystemBus()

        if not self._session_object_path:
            self._setup()

        self._signal_receiver = self._bus.add_signal_receiver(
            handler_function=self.session_unlocked_callback,
            signal_name="Unlock",
            dbus_interface="org.freedesktop.login1.Session",
            bus_name="org.freedesktop.login1",
            path=self._session_object_path,
        )

    def disable(self):
        """Disables user session monitoring"""
        if self._signal_receiver:
            self._signal_receiver.remove()

    @property
    def is_session_unlocked(self):
        """Returns True if the user session is unlocked or False otherwise."""
        return True

    def _setup(self):
        seat_auto_proxy = self._bus.get_object(
            "org.freedesktop.login1",
            "/org/freedesktop/login1/seat/auto"
        )

        seat_auto_properties_proxy = dbus.Interface(
            seat_auto_proxy,
            "org.freedesktop.DBus.Properties"
        )

        # There should always be session for a seat. If there is no seat then
        # it means that the user is not directly controlling the machine,
        # but rather controlloing it via ssh or some other indirect
        # type of control.
        try:

            self._session_object_path = seat_auto_properties_proxy.GetAll(
                "org.freedesktop.login1.Seat"
            ).get("ActiveSession", [])[1]
        except IndexError as e:  # pylint: disable=invalid-name
            raise RuntimeError from e
