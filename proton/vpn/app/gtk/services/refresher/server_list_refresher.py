"""
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
from concurrent.futures import Future, ThreadPoolExecutor
from datetime import timedelta
from typing import Callable

from gi.repository import GLib, GObject

from proton.session.exceptions import (
    ProtonAPINotReachable, ProtonAPINotAvailable,
)

from proton.vpn import logging
from proton.vpn.session.servers.logicals import ServerList
from proton.vpn.core_api.api import ProtonVPNAPI

from proton.vpn.app.gtk.utils.glib import run_after_seconds

logger = logging.getLogger(__name__)


class ServerListRefresher(GObject.Object):
    """
    Service in charge of refreshing the VPN server list/loads.
    """
    def __init__(
            self,
            thread_pool_executor: ThreadPoolExecutor,
            proton_vpn_api: ProtonVPNAPI
    ):
        super().__init__()
        self._thread_pool = thread_pool_executor
        self._api = proton_vpn_api
        self._reload_servers_source_id: int = None

    @GObject.Signal(name="new-server-list", arg_types=(object,))
    def new_server_list(self, server_list: ServerList):
        """Signal emitted when a new server list is available."""

    @GObject.Signal(name="new-server-loads", arg_types=(object,))
    def new_server_loads(self, server_list: ServerList):
        """Signal emitted when the server list is updated with new server loads."""

    @property
    def enabled(self):
        """Whether the refresher has already been enabled or not."""
        return self._reload_servers_source_id is not None

    def enable(self):
        """Starts periodically refreshing the server lists/loads"""
        if not self._api.vpn_session_loaded:
            raise RuntimeError("VPN session was not loaded yet.")

        if self.enabled:
            return

        logger.info("Server list refresher enabled.")
        self._refresh()

    def disable(self):
        """Stops periodically refreshing the server list/loads."""
        if self._reload_servers_source_id is not None:
            GLib.source_remove(self._reload_servers_source_id)
            self._reload_servers_source_id = None
            logger.info("Server list refresher disabled.")

    def _refresh(self):
        """Refreshes the server list/loads if expired, else schedules a future refresh."""
        if self._api.server_list.expired:
            self._trigger_api_call(
                api_method=self._api.fetch_server_list, signal_to_emit="new-server-list"
            )
        elif self._api.server_list.loads_expired:
            self._trigger_api_call(
                api_method=self._api.update_server_loads, signal_to_emit="new-server-loads"
            )
        else:
            self._schedule_next_server_list_refresh(
                delay_in_seconds=self._api.server_list.seconds_until_expiration
            )

    def _trigger_api_call(self, api_method: Callable, signal_to_emit: str) -> Future:
        future = self._thread_pool.submit(api_method)
        future.add_done_callback(
            lambda future: GLib.idle_add(self._on_api_call_done, future, signal_to_emit)
        )
        return future

    def _on_api_call_done(self, future_server_list: Future, signal_to_emit: str):
        # If the server list/loads fetch fails, the next try will always
        # be done after a server loads refresh delay (currently ~15 min).
        next_refresh_delay = ServerList.get_loads_refresh_interval_in_seconds()
        try:
            new_server_list = future_server_list.result()
            next_refresh_delay = new_server_list.seconds_until_expiration
            self.emit(signal_to_emit, new_server_list)
        except (ProtonAPINotReachable, ProtonAPINotAvailable) as error:
            logger.warning(f"Server list refresh failed: {error}")
        finally:
            self._schedule_next_server_list_refresh(
                delay_in_seconds=next_refresh_delay
            )

    def _schedule_next_server_list_refresh(self, delay_in_seconds: float):
        self._reload_servers_source_id = run_after_seconds(
            self._refresh,
            delay_seconds=delay_in_seconds
        )
        logger.info(
            f"Next server list refresh scheduled in "
            f"{timedelta(seconds=delay_in_seconds)}"
        )
