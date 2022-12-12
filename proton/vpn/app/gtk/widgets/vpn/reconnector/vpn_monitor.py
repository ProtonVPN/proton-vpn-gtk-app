"""
VPN connection monitoring.
"""
from typing import Callable, Optional

from proton.vpn.connection import states
from proton.vpn.core_api.connection import VPNConnectionHolder


class VPNMonitor:
    """
    After being enabled, it calls the configured callbacks whenever certain
    VPN events happen.

    Attributes:
        vpn_drop_callback: callable to be called whenever the VPN connection dropped.
        vpn_up_callback: callable to be called whenever the VPN connection is up.
    """

    def __init__(self, vpn_connector: VPNConnectionHolder):
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
