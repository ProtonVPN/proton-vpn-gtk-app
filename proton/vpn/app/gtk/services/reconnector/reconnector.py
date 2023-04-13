"""
Auto reconnect feature.


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
import random
from typing import TYPE_CHECKING

from gi.repository import GLib

from proton.vpn import logging
from proton.vpn.connection import states, VPNConnection
from proton.vpn.core_api.connection import VPNConnectorWrapper

from proton.vpn.app.gtk.services.reconnector.network_monitor import NetworkMonitor
from proton.vpn.app.gtk.services.reconnector.session_monitor import SessionMonitor
from proton.vpn.app.gtk.services.reconnector.vpn_monitor import VPNMonitor

if TYPE_CHECKING:
    from proton.vpn.app.gtk.services import VPNDataRefresher

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

    # pylint: disable=too-many-arguments
    def __init__(
            self,
            vpn_connector: VPNConnectorWrapper,
            vpn_data_refresher: "VPNDataRefresher",
            vpn_monitor: VPNMonitor,
            network_monitor: NetworkMonitor,
            session_monitor: SessionMonitor
    ):
        self._vpn_connector = vpn_connector
        self._vpn_data_refresher = vpn_data_refresher

        self._vpn_monitor = vpn_monitor
        self._vpn_monitor.vpn_drop_callback = self._on_vpn_drop
        self._vpn_monitor.vpn_up_callback = self._on_vpn_up

        self._network_monitor = network_monitor
        self._network_monitor.network_up_callback = self._on_network_up

        self._session_monitor = session_monitor or SessionMonitor()
        self._session_monitor.session_unlocked_callback = self._on_session_unlocked

        self._retry_src_id = None
        self.retry_counter = 0

    @property
    def is_reconnection_scheduled(self) -> bool:
        """Returns True if there is a pending scheduled reconnection and False otherwise."""
        return self._retry_src_id is not None

    def enable(self):
        """Enables the auto reconnect feature."""
        if not self._vpn_data_refresher.is_vpn_data_ready:
            raise RuntimeError("VPN data refresher is not ready.")
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
        return isinstance(self._vpn_connector.current_state, states.Error)

    def schedule_reconnection(self) -> bool:
        """Schedules a reconnection attempt.

        The amount of time elapsed before the reconnection is attempted
        depends on the number of previous failed reconnection attempts.

        :return: True if the reconnection could be scheduled and False otherwise.
        """
        if self._retry_src_id:
            logger.warning("There is already a scheduled VPN reconnection attempt.")
            return False

        retry_delay = self._calculate_retry_delay_in_milliseconds()
        logger.info(
            f"Reconnection attempt #{self.retry_counter} scheduled in "
            f"{retry_delay/1000:.2f} seconds.")
        self._retry_src_id = GLib.timeout_add(retry_delay, self._reconnect)
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

        self.schedule_reconnection()

    def _on_vpn_drop(self):
        """Callback called by the VPN monitor when a VPN connection drop was detected."""
        logger.info("VPN connection drop was detected.")
        self.schedule_reconnection()

    def _on_vpn_up(self):
        """Callback called by the VPN monitor when the VPN connection is up."""
        logger.debug("VPN connection is up.")
        self._reset_retry_counter()

    def _reconnect(self):
        logger.info(f"Reconnecting (attempt #{self.retry_counter})...")
        connection = self._vpn_connector.current_connection

        if not self._network_monitor.is_network_up:
            logger.info("VPN reconnection not possible: network is down.")
            self._increase_retry_counter()
            self.schedule_reconnection()
            return False

        if not self._session_monitor.is_session_unlocked:
            logger.info("VPN reconnection not possible: session is locked.")
            self._increase_retry_counter()
            self.schedule_reconnection()
            return False

        vpn_server = self._get_vpn_server(connection.server_id)
        if vpn_server:
            self._vpn_connector.connect(
                vpn_server,
                connection.protocol,
                connection.backend
            )
            self._increase_retry_counter()
        else:
            # The server was removed from the server list after the user had connected to it.
            logger.warning(
                "VPN Reconnection not possible: logical server not found "
                f"(id = {connection.server_id})"
            )

        return False  # Remove periodic source

    def _get_vpn_server(self, server_id: str):
        logical_server = self._vpn_data_refresher.server_list.get_by_id(server_id)
        if not logical_server:
            return None
        client_config = self._vpn_data_refresher.client_config

        return self._vpn_connector.get_vpn_server(logical_server, client_config)

    def _calculate_retry_delay_in_milliseconds(self) -> int:
        """
        Returns the amount of milliseconds to wait before a VPN connection retry.

        The amount of time increases exponentially based on the number of
        previous attempts.
        """
        return 2 ** self.retry_counter * random.uniform(0.9, 1.1) * 1000

    def _reset_retry_counter(self):
        if self._retry_src_id:
            GLib.source_remove(self._retry_src_id)
            self._retry_src_id = None
        self.retry_counter = 0

    def _increase_retry_counter(self):
        self.retry_counter += 1
        self._retry_src_id = None
