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
from typing import Optional
from concurrent.futures import Future
from datetime import timedelta
from gi.repository import GObject, GLib


from proton.vpn.app.gtk.utils.executor import AsyncExecutor
from proton.vpn.app.gtk.utils.glib import run_after_seconds, cancel_task

from proton.vpn import logging
from proton.vpn.core.api import ProtonVPNAPI
from proton.session.exceptions import (
    ProtonAPINotReachable, ProtonAPINotAvailable,
)

logger = logging.getLogger(__name__)

# pylint: disable=R0801


class CertificateRefresher(GObject.Object):
    """
    Service in charge of refreshing certificate, that is used to derive
    users private keys, to establish VPN connections.
    """
    def __init__(self, executor: AsyncExecutor, proton_vpn_api: ProtonVPNAPI):
        super().__init__()
        self._executor = executor
        self._api = proton_vpn_api
        self._refresh_task_id: Optional[int] = None

    @GObject.Signal(name="new-certificate")
    def new_certificate(self):
        """Signal emitted when just after the certificate was refreshed."""

    @property
    def enabled(self):
        """Whether the refresher has already been enabled or not."""
        return self._refresh_task_id is not None

    def enable(self):
        """Starts periodically refreshing the client configuration."""
        if self.enabled:
            return

        if not self._api.vpn_session_loaded:
            raise RuntimeError("VPN session was not loaded yet.")

        logger.info("Certificate refresher enabled.")
        delay_in_seconds = self._api.account_data\
            .vpn_credentials\
            .pubkey_credentials\
            .remaining_time_to_next_refresh
        self._schedule_next_certificate_refresh(
            delay_in_seconds=delay_in_seconds
        )

    def disable(self):
        """Stops refreshing the client configuration."""
        self._unschedule_next_refresh()
        logger.info("Certificate refresher disabled")

    def _refresh(self):
        """Fetches the new certificate from the REST API."""
        future = self._executor.submit(self._api.fetch_certificate)
        future.add_done_callback(
            lambda f: GLib.idle_add(
                self._on_certificate_retrieved, f
            )
        )
        return future

    def _on_certificate_retrieved(self, future_certificate: Future):
        next_refresh_delay = self._api.account_data\
            .vpn_credentials.pubkey_credentials.get_refresh_interval_in_seconds()
        try:
            future_certificate.result()
            next_refresh_delay = self._api.account_data\
                .vpn_credentials.pubkey_credentials.remaining_time_to_next_refresh
            self.emit("new-certificate")
        except (ProtonAPINotReachable, ProtonAPINotAvailable) as error:
            logger.warning(f"Certificate refresh failed: {error}")
        finally:
            self._schedule_next_certificate_refresh(
                delay_in_seconds=next_refresh_delay
            )

    def _schedule_next_certificate_refresh(self, delay_in_seconds: float):
        self._refresh_task_id = run_after_seconds(
            self._refresh,
            delay_seconds=delay_in_seconds
        )

        logger.info(
            "Next certificate refresh scheduled in "
            f"{timedelta(seconds=delay_in_seconds)}"
        )

    def _unschedule_next_refresh(self):
        if not self.enable:
            return

        cancel_task(self._refresh_task_id)
        self._refresh_task_id = None
