"""
Certain VPN data like the server list and the client configuration needs to
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
from typing import Callable, Any, Dict

from gi.repository import GLib, GObject

from proton.vpn import logging
from proton.vpn.session.client_config import ClientConfig
from proton.vpn.session.servers.logicals import ServerList
from proton.vpn.core.api import ProtonVPNAPI

from proton.vpn.app.gtk.services.refresher.client_config_refresher import ClientConfigRefresher
from proton.vpn.app.gtk.services.refresher.server_list_refresher import ServerListRefresher
from proton.vpn.app.gtk.utils.executor import AsyncExecutor

logger = logging.getLogger(__name__)


class VPNDataRefresher(GObject.Object):
    """
    Service in charge of:
        - retrieving the required VPN data from Proton's REST API
          to be able to establish VPN connection,
        - keeping it up to date and
        - notifying subscribers when VPN data has been updated.
    """
    def __init__(
        self,
        executor: AsyncExecutor,
        proton_vpn_api: ProtonVPNAPI,
        client_config_refresher: ClientConfigRefresher = None,
        server_list_refresher: ServerListRefresher = None
    ):
        super().__init__()
        self._executor = executor
        self._api = proton_vpn_api
        self._client_config_refresher = client_config_refresher or ClientConfigRefresher(
            executor,
            proton_vpn_api
        )
        self._server_list_refresher = server_list_refresher or ServerListRefresher(
            executor,
            proton_vpn_api
        )
        self._signal_refresher_map = {
            "new-client-config": self._client_config_refresher,
            "new-server-list": self._server_list_refresher,
            "new-server-loads": self._server_list_refresher
        }
        self._signal_handler_ids: Dict[int, GObject.Object] = {}

    @property
    def server_list(self) -> ServerList:
        """
        Returns the list of available VPN servers.
        """
        return self._api.server_list

    @property
    def client_config(self) -> ClientConfig:
        """Returns the VPN client configuration."""
        return self._api.client_config

    @GObject.Signal(name="vpn-data-ready", arg_types=(object, object))
    def vpn_data_ready(self, server_list: ServerList, client_config: ClientConfig):
        """Signal emitted when all the required VPN data to run the app
        has been downloaded from the REST API."""

    # pylint: disable=arguments-differ
    def connect(
        self, detailed_signal: str, handler: Callable[..., Any], *args: Any
    ) -> int:
        """Overrides GObject.Object.connect to pass through some of the calls
        to child refreshers."""

        refresher = self._signal_refresher_map.get(detailed_signal, super())
        handler_id = refresher.connect(detailed_signal, handler, *args)
        # Keep track of the object a handler id came from to be able to disconnect it.
        self._signal_handler_ids[handler_id] = refresher

        return handler_id

    def disconnect(self, id: int) -> None:  # pylint: disable=arguments-differ,redefined-builtin
        """Overrides GObject.Object.disconnect to pass through some of the calls
        to child refreshers."""
        refresher = self._signal_handler_ids.get(id, super())
        refresher.disconnect(id)
        del self._signal_handler_ids[id]

    def emit(self, detailed_signal: str, *args, **kwargs):
        """Overrides GObject.Object.emit to pass through some of the calls
        to child refreshers."""
        refresher = self._signal_refresher_map.get(detailed_signal, super())
        refresher.emit(detailed_signal, *args, **kwargs)

    @property
    def is_vpn_data_ready(self) -> bool:
        """Returns whether the necessary data from API has already been retrieved or not."""
        return self._api.vpn_session_loaded

    def enable(self):
        """Start retrieving data periodically from Proton's REST API."""
        if self._api.vpn_session_loaded:
            self._enable()
        else:
            # The VPN session is normally loaded straight after the user logs in. However,
            # it could happen that it's not loaded in any of the following scenarios:
            # a) After a successful authentication, the HTTP requests to retrieve
            #    the required VPN session data failed, so it was never persisted.
            # b) The persisted VPN session does not have the expected format.
            #    This can happen if we introduce a breaking change or if the persisted
            #    data is messed up because the user changes it, or it gets corrupted.
            self._refresh_vpn_session_and_then_enable()

    def disable(self):
        """Stops retrieving data periodically from Proton's REST API."""
        self._client_config_refresher.disable()
        self._server_list_refresher.disable()
        logger.info(
            "VPN data refresher service disabled.",
            category="app", subcategory="vpn_data_refresher", event="disable"
        )

    def _enable(self):
        self.emit("vpn-data-ready", self._api.server_list, self._api.client_config)
        logger.info(
            "VPN data refresher service enabled.",
            category="app", subcategory="vpn_data_refresher", event="enable"
        )
        self._client_config_refresher.enable()
        self._server_list_refresher.enable()

    def _refresh_vpn_session_and_then_enable(self):
        logger.warning("Reloading VPN session...")
        on_vpn_session_ready_future = self._executor.submit(
            self._api.fetch_session_data
        )

        def on_vpn_session_ready(future):
            future.result()
            self._enable()

        on_vpn_session_ready_future.add_done_callback(
            lambda f: GLib.idle_add(on_vpn_session_ready, f)
        )
