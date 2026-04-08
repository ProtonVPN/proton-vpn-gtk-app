"""
User session monitoring.


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
from typing import Callable, Optional

from proton.vpn.app.gtk.services.reconnector.login_session_service import LoginSessionService


class SessionMonitor:
    """
    After being enabled, it calls the callback set on the
    session_unlocked_callback attribute whenever the user session was unlocked.

    Attributes:
        session_unlocked_callback: callable that will be called when the user
        session is unlocked.
    """

    def __init__(self, login_session_service: LoginSessionService = None):
        self._login_session_service = login_session_service or LoginSessionService()
        self._signal_receiver: Optional[object] = None
        self.session_unlocked_callback: Optional[Callable] = None

    def enable(self):
        """Enables user session monitoring."""
        if not callable(self.session_unlocked_callback):
            raise RuntimeError("Callback was not set")

        try:
            self._signal_receiver = \
                self._login_session_service.add_session_unlocked_signal_receiver(
                    self.session_unlocked_callback
                )
        except LoginSessionService.DBusUnavailableError:
            # logind is inaccessible (e.g. AppArmor in strict snap confinement).
            # Session-unlock reconnection won't work, but everything else is fine.
            pass

    def disable(self):
        """Disables user session monitoring."""
        if self._signal_receiver:
            self._signal_receiver.remove()
            self._signal_receiver = None

    @property
    def is_session_unlocked(self) -> bool:
        """Returns True if the user session is unlocked or False otherwise."""
        try:
            return self._login_session_service.is_session_unlocked
        except LoginSessionService.DBusUnavailableError:
            # logind is inaccessible; assume session is unlocked so reconnection
            # can proceed when network comes up.
            return True

    def set_signal_receiver(self, new_object: Optional[object]):
        """Sets signal receiver.
        This is mainly used for testing purposes.
        """
        self._signal_receiver = new_object
