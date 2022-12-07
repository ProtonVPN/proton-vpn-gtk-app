"""
Auto reconnect feature.
"""
from proton.vpn import logging
from proton.vpn.connection import events, states, VPNConnection
from proton.vpn.core_api.connection import VPNConnectionHolder

from proton.vpn.app.gtk.services.reconnector.network_monitor import NetworkMonitor
from proton.vpn.app.gtk.services.reconnector.session_monitor import SessionMonitor
from proton.vpn.app.gtk.services.reconnector.vpn_monitor import VPNMonitor

logger = logging.getLogger(__name__)


class VPNReconnector:
    """
    It implements the auto reconnect feature.

    The reconnector is in charge of reconnecting the current Proton VPN connection
    when it drops.

    Currently, it requires a GLib MainLoop to be running. In a future version,
    the reconnector will be refactored so that it runs in a separate python
    process and will run its own main loop.
    """

    def __init__(
            self,
            vpn_connector: VPNConnectionHolder,
            vpn_monitor: VPNMonitor = None,
            network_monitor: NetworkMonitor = None,
            session_monitor: SessionMonitor = None
    ):
        self._vpn_connector = vpn_connector

        self._vpn_monitor = vpn_monitor or VPNMonitor(vpn_connector)
        self._vpn_monitor.vpn_drop_callback = self._on_vpn_drop
        self._vpn_monitor.vpn_up_callback = self._on_vpn_up

        self._network_monitor = network_monitor or NetworkMonitor()
        self._network_monitor.network_up_callback = self._on_network_up

        self._session_monitor = session_monitor or SessionMonitor()
        self._session_monitor.session_unlocked_callback = self._on_session_unlocked

    def enable(self):
        """Enables the auto reconnect feature."""
        self._vpn_monitor.enable()
        self._network_monitor.enable()
        self._session_monitor.enable()
        logger.info("VPN reconnector enabled.")

    def disable(self):
        """Disables the auto reconnect feature."""
        self._vpn_monitor.disable()
        self._network_monitor.disable()
        self._session_monitor.disable()
        logger.info("VPN reconnector disabled.")

    @property
    def did_vpn_drop(self) -> bool:
        """Returns True if the VPN connection dropped or False otherwise."""
        if not self._current_connection:
            return False

        return isinstance(self._current_connection.status, states.Error)

    @property
    def is_reconnection_possible(self):
        """Returns True if all resources required to be able to reconnect are
        available, or False otherwise."""
        if not self._current_connection:
            logger.info("VPN reconnection was not possible: "
                        "there is not an existing VPN connection.")
            return False

        if not self._session_monitor.is_session_unlocked:
            logger.info("VPN reconnection was not possible: the user's session is locked.")
            return False

        if not self._network_monitor.is_network_up:
            logger.info("VPN reconnection was not possible: there is not network connectivity.")
            return False

        return True

    def reconnect(self) -> bool:
        """Runs a reconnection attempt.
        :return: True if the reconnection could be initiated and False otherwise.
        """
        if not self.is_reconnection_possible:
            return True

        disconnection_event = self._current_connection.status.context.event
        if not isinstance(disconnection_event, (
                events.DeviceDisconnected, events.Timeout
        )):
            logger.error("VPN reconnection not implemented for the following "
                         f"disconnection event: {disconnection_event}")
            return False

        self._reconnect()
        return True

    @property
    def _current_connection(self) -> VPNConnection:
        return self._vpn_connector.current_connection

    def _on_session_unlocked(self):
        """
        Callback called once the user session has been unlocked.
        """
        logger.info("Session unlocked")
        if self.did_vpn_drop:
            self.reconnect()

    def _on_network_up(self):
        """
        Callback called by the network monitor once the machine's network state
        reaches the connected state, meaning that from now on is able to reach
        the internet.
        """
        logger.info("Network connectivity was detected.")
        if self.did_vpn_drop:
            self.reconnect()

    def _on_vpn_drop(self):
        """Callback called by the VPN monitor when a VPN connection drop was detected."""
        logger.info("VPN connection drop was detected.")

    def _on_vpn_up(self):
        """Callback called by the VPN monitor when the VPN connection is up."""
        logger.debug("VPN connection is up.")

    def _reconnect(self):
        logger.info("Reconnecting...")
        connection = self._vpn_connector.current_connection
        self._vpn_connector.connect(
            connection._vpnserver,  # pylint: disable=protected-access
            connection.protocol,
            connection.backend
        )
