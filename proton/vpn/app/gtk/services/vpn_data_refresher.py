"""
Certain VPN data like the server list or the client configuration needs to
refreshed periodically to keep it up to date.

This module defines the required services to do so.


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
from dataclasses import dataclass

from gi.repository import GLib, GObject

from proton.session.exceptions import (
    ProtonAPINotReachable, ProtonAPINotAvailable,
)
from proton.vpn.servers.list import ServerList
from proton.vpn.core_api.api import ProtonVPNAPI
from proton.vpn.core_api.client_config import ClientConfig
from proton.vpn import logging


logger = logging.getLogger(__name__)

# Number of seconds to wait before checking if the cache is expired.
CACHE_EXPIRATION_CHECK_INTERVAL_IN_SECONDS = 60


@dataclass
class VPNDataRefresherState:
    """
    Contextual data that is kept about the current user session. All this data
    is reset after a logout/login.
    """
    api_data_retrieval_complete = False
    reload_servers_source_id: int = None
    reload_client_config_source_id: int = None
    client_config: ClientConfig = None
    server_list: ServerList = None
    last_server_list_update_time: int = 0


class VPNDataRefresher(GObject.Object):
    """
    Service in charge of:
        - retrieving the required VPN data from Proton's REST API
          to be able to establish VPN connection,
        - keeping it up to date and
        - notifying subscribers when VPN data has been updated.

    Attributes:
        server_list: List of VPN servers to be presented to the user.
        client_config: VPN client configuration to be able to establish a VPN
        connection to any of the available servers.
    """
    def __init__(
        self,
        thread_pool_executor: ThreadPoolExecutor,
        proton_vpn_api: ProtonVPNAPI,
        state: VPNDataRefresherState = None
    ):
        super().__init__()
        self._thread_pool = thread_pool_executor
        self._api = proton_vpn_api
        self._state = state or VPNDataRefresherState()

    @property
    def server_list(self) -> ServerList:
        """
        Returns the list of available VPN servers.
        """
        return self._state.server_list

    @server_list.setter
    def server_list(self, server_list: ServerList):
        """Sets the list of available VPN servers."""
        self._state.server_list = server_list

    @property
    def client_config(self) -> ClientConfig:
        """Returns the VPN client configuration."""
        return self._state.client_config

    @client_config.setter
    def client_config(self, client_config: ClientConfig):
        """Sets the VPN client configuration."""
        self._state.client_config = client_config

    @GObject.Signal(name="new-server-list", arg_types=(object,))
    def new_server_list(self, server_list: ServerList):
        """Signal emitted when the VPN server list has been updated."""

    @GObject.Signal(name="new-client-config", arg_types=(object,))
    def new_client_config(self, client_config: ClientConfig):
        """Signal emitted when the VPN client configuration has been updated."""

    @GObject.Signal(name="vpn-data-ready", arg_types=(object, object))
    def vpn_data_ready(self, server_list: ServerList, client_config: ClientConfig):
        """Signal emitted when the VPN client configuration has been updated."""

    @property
    def is_vpn_data_ready(self) -> bool:
        """Returns whether the necessary data from API has already been retrieved or not."""
        return bool(self.server_list and self.client_config)

    def enable(self):
        """Start retrieving data periodically from Proton's REST API."""
        if self._api.vpn_account:
            self._enable()
        else:
            # The VPN account is normally loaded straight after the user logs in. However,
            # could happen that it's not loaded in any of the following scenarios:
            # a) After a successful authentication, the HTTP requests to retrieve
            #    the VPN account failed, so it was never stored in the keyring.
            # b) The VPN account stored in the keyring does not have the expected format.
            #    This can happen if we introduce a breaking change or if the keyring
            #    data is messed up because the user changes it, or it gets corrupted.
            self._refresh_vpn_account_and_then_enable()

    def _enable(self):
        self._enable_client_config_refresh()
        self._enable_server_list_refresh()
        logger.info(
            "VPN data refresher service enabled.",
            category="app", subcategory="vpn_data_refresher", event="enable"
        )

    def _refresh_vpn_account_and_then_enable(self):
        logger.warning("Refreshing VPN account since it was not found...")
        on_vpn_account_ready_future = self._thread_pool.submit(
            self._api.refresh_vpn_account
        )

        def on_vpn_account_ready(future):
            future.result()
            self._enable()

        on_vpn_account_ready_future.add_done_callback(
            lambda f: GLib.idle_add(on_vpn_account_ready, f)
        )

    def disable(self):
        """Stops retrieving data periodically from Proton's REST API."""
        self._disable_client_config_refresh()
        self._disable_server_list_refresh()
        self._state = VPNDataRefresherState()
        logger.info(
            "VPN data refresher service disabled.",
            category="app", subcategory="vpn_data_refresher", event="disable"
        )

    def _enable_server_list_refresh(self):
        """Schedules periodic API calls to refresh the server list."""
        future_server_list = self._get_cached_server_list()
        # After the server list is retrieved from cache (if existing),
        # start updating it periodically with data retrieved from the API.
        future_server_list.add_done_callback(
            lambda f: GLib.idle_add(
                self._refresh_server_list_periodically
            )
        )

    def _enable_client_config_refresh(self):
        """Schedules periodic API calls to refresh the client configuration."""
        future_client_config = self._get_cached_client_config()
        # After the client config is retrieved from cache (if existing),
        # start updating it periodically with data retrieved from the API.
        future_client_config.add_done_callback(
            lambda f: GLib.idle_add(
                self._refresh_client_config_periodically
            )
        )

    def _disable_client_config_refresh(self):
        if self._state.reload_client_config_source_id is not None:
            GLib.source_remove(self._state.reload_client_config_source_id)
            self._state.reload_client_config_source_id = None

    def _disable_server_list_refresh(self):
        if self._state.reload_servers_source_id is not None:
            GLib.source_remove(self._state.reload_servers_source_id)
            self._state.reload_servers_source_id = None

    def _refresh_client_config_periodically(self):
        self.get_fresh_client_config()
        self._state.reload_client_config_source_id = GLib.timeout_add(
            interval=CACHE_EXPIRATION_CHECK_INTERVAL_IN_SECONDS * 1000,
            function=self.get_fresh_client_config
        )

    def _get_cached_client_config(self) -> Future:
        future = self._thread_pool.submit(self._api.get_cached_client_config)
        future.add_done_callback(lambda f: GLib.idle_add(
            self._on_client_config_retrieved, f
        ))
        return future

    def _refresh_server_list_periodically(self):
        self.get_fresh_server_list()
        self._state.reload_servers_source_id = GLib.timeout_add(
            interval=CACHE_EXPIRATION_CHECK_INTERVAL_IN_SECONDS * 1000,
            function=self.get_fresh_server_list
        )

    def _get_cached_server_list(self):
        future = self._thread_pool.submit(self._api.servers.get_cached_server_list)
        future.add_done_callback(lambda f: GLib.idle_add(
            self._on_server_list_retrieved, f
        ))
        return future

    def get_fresh_client_config(self) -> Future:
        """Returns client config."""
        logger.debug(
            "Retrieving client configuration...",
            category="api", subcategory="client_config", event="get"
        )
        future = self._thread_pool.submit(
            self._api.get_fresh_client_config,
            force_refresh=False
        )
        future.add_done_callback(
            lambda f: GLib.idle_add(
                self._on_client_config_retrieved, f
            )
        )
        return future

    def get_fresh_server_list(self) -> Future:
        """
        Requests the list of servers. Note that a remote API call is only
        triggered if the server list cache expired.
        :return: A future wrapping the server list.
        """
        logger.debug(
            "Retrieving server list...",
            category="api", subcategory="logicals", event="get"
        )
        future = self._thread_pool.submit(
            self._api.servers.get_fresh_server_list,
            force_refresh=False
        )
        future.add_done_callback(
            lambda future: GLib.idle_add(self._on_server_list_retrieved, future)
        )
        return future

    def _on_client_config_retrieved(self, future_client_config: Future):
        new_client_config = self._handle_api_response(
            future=future_client_config,
            log_message="Client config update failed",
            subcategory="clientconfig"
        )

        if not new_client_config:
            # Client config cache did not exist.
            return

        if new_client_config is not self.client_config:
            self.client_config = new_client_config
            self.emit("new-client-config", self.client_config)
            self._emit_signal_once_all_required_vpn_data_is_available()
        else:
            logger.debug(
                "Skipping client configuration reload because it's already up "
                "to date.", category="app", subcategory="client_config",
                event="get"
            )

    def _on_server_list_retrieved(self, future_server_list: Future):
        server_list = self._handle_api_response(
            future=future_server_list,
            log_message="Server list update failed",
            subcategory="servers"
        )

        if not server_list:
            # Server list cache did not exist.
            return

        if self._is_server_list_outdated(server_list):
            self.server_list = server_list
            self._state.last_server_list_update_time = server_list.loads_update_timestamp
            self.emit("new-server-list", server_list)
            self._emit_signal_once_all_required_vpn_data_is_available()
        else:
            logger.debug(
                "Skipping server list update because it's already up to date.",
                category="app", subcategory="servers", event="reload"
            )

    def _handle_api_response(self, future: Future, log_message: str, subcategory: str):
        data = None

        try:
            data = future.result()
        except (
            ProtonAPINotReachable,
            ProtonAPINotAvailable
        ) as error:
            logger.warning(
                f"{log_message}: {error}",
                category="app", subcategory=f"{subcategory}", event="get"
            )

        return data

    def _emit_signal_once_all_required_vpn_data_is_available(self):
        if not self._state.api_data_retrieval_complete and self.is_vpn_data_ready:
            self.emit("vpn-data-ready", self.server_list, self.client_config)
            self._state.api_data_retrieval_complete = True

    def _is_server_list_outdated(self, new_server_list: ServerList):
        """Returns if server list is outdated or not."""
        new_timestamp = new_server_list.loads_update_timestamp
        return self._state.last_server_list_update_time < new_timestamp
