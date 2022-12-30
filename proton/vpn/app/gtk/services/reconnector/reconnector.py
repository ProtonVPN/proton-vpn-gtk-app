"""
Auto reconnect feature.
"""
import random

from gi.repository import GLib

from proton.vpn import logging
from proton.vpn.connection import states, VPNConnection
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

        self._retry_src_id = None
        self._retry_counter = 0

    def enable(self):
        """Enables the auto reconnect feature."""
        self._reset_retry_counter()
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

    def schedule_reconnection(self) -> bool:
        """Schedules a reconnection attempt.

        The amount of time elapsed before the reconnection is attempted
        depends on the number of previous failed reconnection attempts.

        :return: True if the reconnection could be scheduled and False otherwise.
        """
        if self._retry_src_id:
            logger.warning("There is already a scheduled VPN reconnection attempt.")
            return False

        retry_delay = self._calculate_retry_delay_in_seconds()
        logger.info(
            f"Reconnection attempt #{self._retry_counter} scheduled in "
            f"{retry_delay:.2f} seconds.")
        self._retry_src_id = GLib.timeout_add_seconds(retry_delay, self._reconnect)
        return True

    @property
    def _current_connection(self) -> VPNConnection:
        return self._vpn_connector.current_connection

    def _on_session_unlocked(self):
        """
        Callback called by the session monitor once the user session has been
        unlocked.
        """
        logger.info("Session unlocked.")
        self._reset_retry_counter()

        if not self.did_vpn_drop:
            logger.debug("VPN reconnection not necessary: connection didn't drop.")
            return

        if not self._network_monitor.is_network_up:
            logger.info("VPN reconnection not possible: network is down.")
            return

        self.schedule_reconnection()

    def _on_network_up(self):
        """
        Callback called by the network monitor once the machine's network state
        reaches the connected state, meaning that from now on is able to reach
        the internet.
        """
        logger.info("Network connectivity was detected.")
        self._reset_retry_counter()

        if not self.did_vpn_drop:
            logger.debug("VPN reconnection not necessary: connection didn't drop.")
            return

        if not self._session_monitor.is_session_unlocked:
            logger.info("VPN reconnection not possible: session is locked.")
            return

        self.schedule_reconnection()

    def _on_vpn_drop(self):
        """Callback called by the VPN monitor when a VPN connection drop was detected."""
        logger.info("VPN connection drop was detected.")
        if self._retry_src_id:
            GLib.source_remove(self._retry_src_id)
            self._retry_src_id = None
        self.schedule_reconnection()

    def _on_vpn_up(self):
        """Callback called by the VPN monitor when the VPN connection is up."""
        logger.debug("VPN connection is up.")
        self._reset_retry_counter()

    def _reconnect(self):
        logger.info(f"Reconnecting (attempt #{self._retry_counter})...")

        connection = self._vpn_connector.current_connection
        self._vpn_connector.connect(
            connection._vpnserver,  # pylint: disable=protected-access
            connection.protocol,
            connection.backend
        )
        self._retry_counter += 1
        self._retry_src_id = None

        return False  # Remove periodic source

    def _calculate_retry_delay_in_seconds(self) -> int:
        """
        Returns the amount of seconds to wait before a VPN connection retry.

        The amount of time increases exponentially based on the number of
        previous attempts.
        """
        return 2 ** self._retry_counter * random.uniform(0.9, 1.1)

    def _reset_retry_counter(self):
        if self._retry_src_id:
            GLib.source_remove(self._retry_src_id)
            self._retry_src_id = None
        self._retry_counter = 0
