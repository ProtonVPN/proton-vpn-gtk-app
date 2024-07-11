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
from proton.vpn.session import FeatureFlags

from proton.vpn import logging
from proton.session.exceptions import (
    ProtonAPINotReachable, ProtonAPINotAvailable,
)

from proton.vpn.app.gtk.utils.executor import AsyncExecutor
from proton.vpn.app.gtk.utils.glib import run_after_seconds, cancel_task

logger = logging.getLogger(__name__)

# pylint: disable=R0801


class FeatureFlagsRefresher(GObject.Object):
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
        self._refresh_task_id: int = None

    @GObject.Signal(name="new-feature-flags")
    def new_feature_flags(self):
        """Signal emitted just after features were refreshed."""

    @property
    def enabled(self):
        """Whether the refresher has already been enabled or not."""
        return self._refresh_task_id is not None

    def enable(self):
        """Starts periodically refreshing."""
        if self.enabled:
            return

        if not self._api.vpn_session_loaded:
            raise RuntimeError("VPN session was not loaded yet.")

        logger.info("Features refresher enabled.")

        self._schedule_next_refresh(
            delay_in_seconds=self._api.feature_flags.seconds_until_expiration
        )

    def disable(self):
        """Stops refreshing."""
        self._unschedule_next_refresh()
        logger.info("Features flags refresher disabled.")

    def _refresh(self) -> Future:
        """Fetches the new features from the REST API."""
        future = self._executor.submit(self._api.fetch_feature_flags)
        future.add_done_callback(
            lambda f: GLib.idle_add(
                self._on_retrieved, f
            )
        )
        return future

    def _on_retrieved(self, future: Future):
        next_refresh_delay = FeatureFlags.get_refresh_interval_in_seconds()
        try:
            new_data = future.result()
            next_refresh_delay = new_data.seconds_until_expiration
            self.emit("new-feature-flags")
        except (ProtonAPINotReachable, ProtonAPINotAvailable) as error:
            logger.warning(f"Features flags update failed: {error}")
        finally:
            self._schedule_next_refresh(
                delay_in_seconds=next_refresh_delay
            )

    def _schedule_next_refresh(self, delay_in_seconds: float):
        self._refresh_task_id = run_after_seconds(
            self._refresh,
            delay_seconds=delay_in_seconds
        )
        logger.info(
            f"Next features flags refresh scheduled in "
            f"{timedelta(seconds=delay_in_seconds)}"
        )

    def _unschedule_next_refresh(self):
        if not self.enabled:
            return

        cancel_task(self._refresh_task_id)
        self._refresh_task_id = None
