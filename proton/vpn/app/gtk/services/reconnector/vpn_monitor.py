"""
VPN connection monitoring.


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

from proton.vpn.connection import states
from proton.vpn.core_api.connection import VPNConnectorWrapper


class VPNMonitor:
    """
    After being enabled, it calls the configured callbacks whenever certain
    VPN events happen.

    Attributes:
        vpn_drop_callback: callable to be called whenever the VPN connection dropped.
        vpn_up_callback: callable to be called whenever the VPN connection is up.
    """

    def __init__(self, vpn_connector: VPNConnectorWrapper):
        self._vpn_connector = vpn_connector
        self.vpn_drop_callback: Optional[Callable] = None
        self.vpn_up_callback: Optional[Callable] = None

    def enable(self):
        """Enables VPN connection monitoring."""
        self._vpn_connector.register(self)

    def disable(self):
        """Disabled VPN connection monitoring."""
        self._vpn_connector.unregister(self)

    def status_update(self, connection_status):
        """This method is called by the VPN connection state machine whenever
        the connection state changes."""
        if isinstance(connection_status, states.Error) and self.vpn_drop_callback:
            self.vpn_drop_callback()  # pylint: disable=not-callable

        if isinstance(connection_status, states.Connected) and self.vpn_up_callback:
            self.vpn_up_callback()  # pylint: disable=not-callable
