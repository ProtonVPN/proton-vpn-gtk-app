"""
Automatic port forwarding feature.


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
import natpmp

from gi.repository import GLib

from proton.vpn import logging
from proton.vpn.connection import states, VPNConnection, events
from proton.vpn.connection.exceptions import VPNConnectionError, AuthenticationError
from proton.vpn.core.connection import VPNConnectorWrapper

from proton.vpn.app.gtk.services.reconnector.network_monitor import NetworkMonitor
from proton.vpn.app.gtk.services.reconnector.session_monitor import SessionMonitor
from proton.vpn.app.gtk.services.reconnector.vpn_monitor import VPNMonitor
from proton.vpn.app.gtk.utils.executor import AsyncExecutor


class VPNPortForwarder:
    """
    This implements the automatic port forwarding feature.

    It uses natpmp to port forward, and must be already connected to a port forwarding server to work.

    Currently, it requires a GLib MainLoop to be running. In a future version,
    the port forwarder will be refactored so that it runs in a separate python
    process and will run its own main loop.
    """

    # pylint: disable=too-many-arguments
    def __init__(
            self,
            vpn_connector: VPNConnectorWrapper,
            vpn_data_refresher: "VPNDataRefresher",
            vpn_monitor: VPNMonitor,
            session_monitor: SessionMonitor,
            async_executor: AsyncExecutor
    ):
        self._vpn_connector = vpn_connector
        self._vpn_data_refresher = vpn_data_refresher

        self._vpn_monitor = vpn_monitor
        self._vpn_monitor.vpn_drop_callback = self._on_vpn_drop
        self._vpn_monitor.vpn_up_callback = self._on_vpn_up

        self._session_monitor = session_monitor or SessionMonitor()
        self._session_monitor.session_unlocked_callback = self._on_session_unlocked

        self._executor = async_executor

        self._interval_src_id = None

        self.interval = 45
        self.error = False
        self.enabled = False
        self.port = None

    def _port_forward():
        try:
            udp_response = natpmp.map_udp_port(public_port=1, private_port=0,
                                               lifetime=60, gateway_ip="10.2.0.1")
            tcp_response = natpmp.map_tcp_port(public_port=1, private_port=0,
                                               lifetime=60, gateway_ip="10.2.0.1")
            udp_port = udp_response.public_port
            tcp_port = udp_response.public_port
        except Exception as exception:
            # log exception and show error message
            logger.error(f"Automatic port forwarding failed: {error}")
            self._error()
        else:
            if udp_port != tcp_port:
                logger.error(f"Automatic port forwarding detected different UDP and TCP ports "
                             f"(UDP port {udp_port} and TCP port {tcp_port}), aborting.")
            else:
                logger.debug(f"Automatically forwarded port {udp_port}.")
                self.port = udp_port

    def _port_forward_interval(self):
        if not self.running:
            return
        self._port_forward()
        # check again, in case there was an error
        if not self.running:
            return
        self._interval_src_id = GLib.timeout_add(self.interval)

    def _stop(self):
        """Stops the port forwarding task if it exists."""
        if self._interval_src_id is not None:
            GLib.source_remove(self._interval_src_id)
            self._interval_src_id = None
        self._port = None

    def _start(self):
        """Starts the port forwarding interval."""
        self._stop()
        self._interval_src_id = GLib.idle_add(self._port_forward_interval)

    @property
    def running(self):
        return self.enabled and not self.error

    def enable(self):
        """Enables the automatic port forwarding feature."""
        self.enabled = True
        self.error = False
        if self.is_valid_server():
            self._start()
            logger.info("Automatic port forwarder enabled.")
        else:
            self._error()
            logger.error("Automatic port forwarding was enabled on an invalid server.")

    def disable(self):
        """Disables the automatic port forwarding feature."""
        self._stop()
        self.enabled = False
        self.error = False
        logger.info("Automatic port forwarder disabled.")

    def _error(self):
        """
        Enters errored state, and stops attempting to forward ports.
        Does NOT log anything, the caller is responsible for that.
        """
        self._stop()
        self.port = None
        self.error = True

    def is_valid_connection(self):
        """
        Returns True if automatic port forwarding is possible or False otherwise.
        """
        # TODO: check if the server is PTP
        return (
            isinstance(self._vpn_connector.current_state, states.Error)
        )
