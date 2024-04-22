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
from concurrent.futures import Future
from datetime import timedelta

from gi.repository import GLib, GObject
from proton.vpn.core.api import ProtonVPNAPI
from proton.vpn.core.session.client_config import ClientConfig

from proton.vpn import logging
from proton.session.exceptions import (
    ProtonAPINotReachable, ProtonAPINotAvailable,
)

from proton.vpn.app.gtk.utils.executor import AsyncExecutor
from proton.vpn.app.gtk.utils.glib import run_after_seconds

logger = logging.getLogger(__name__)


class ClientConfigRefresher(GObject.Object):
    """
    Service in charge of refreshing VPN client configuration data.
    """
    def __init__(
            self,
            executor: AsyncExecutor,
            proton_vpn_api: ProtonVPNAPI
    ):
        super().__init__()
        self._executor = executor
        self._api = proton_vpn_api
        self._reload_client_config_source_id: int = None

    @GObject.Signal(name="new-client-config", arg_types=(object,))
    def new_client_config(self, client_config: ClientConfig):
        """Signal emitted just after VPN client configuration was refreshed."""

    @property
    def enabled(self):
        """Whether the refresher has already been enabled or not."""
        return self._reload_client_config_source_id is not None

    def enable(self):
        """Starts periodically refreshing the client configuration."""
        if self.enabled:
            return

        if not self._api.vpn_session_loaded:
            raise RuntimeError("VPN session was not loaded yet.")

        logger.info("Client config refresher enabled.")

        self._schedule_next_client_config_refresh(
            delay_in_seconds=self._api.client_config.seconds_until_expiration
        )

    def disable(self):
        """Stops refreshing the client configuration."""
        self._unschedule_next_refresh()
        logger.info("Client config refresher disabled.")

    def _refresh(self) -> Future:
        """Fetches the new client configuration from the REST API."""
        future = self._executor.submit(self._api.fetch_client_config)
        future.add_done_callback(
            lambda f: GLib.idle_add(
                self._on_client_config_retrieved, f
            )
        )
        return future

    def _on_client_config_retrieved(self, future_client_config: Future):
        next_refresh_delay = ClientConfig.get_refresh_interval_in_seconds()
        try:
            new_client_config = future_client_config.result()
            next_refresh_delay = new_client_config.seconds_until_expiration
            self.emit("new-client-config", new_client_config)
        except (ProtonAPINotReachable, ProtonAPINotAvailable) as error:
            logger.warning(f"Client config update failed: {error}")
        finally:
            self._schedule_next_client_config_refresh(
                delay_in_seconds=next_refresh_delay
            )

    def _schedule_next_client_config_refresh(self, delay_in_seconds: float):
        self._reload_client_config_source_id = run_after_seconds(
            self._refresh,
            delay_seconds=delay_in_seconds
        )
        logger.info(
            f"Next client config refresh scheduled in "
            f"{timedelta(seconds=delay_in_seconds)}"
        )

    def _unschedule_next_refresh(self):
        if not self.enabled:
            return

        GLib.source_remove(self._reload_client_config_source_id)
        self._reload_client_config_source_id = None
