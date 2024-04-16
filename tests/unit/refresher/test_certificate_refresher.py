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
from threading import Event
from unittest.mock import Mock, patch

from proton.vpn.app.gtk.services.refresher.certificate_refresher import CertificateRefresher
from tests.unit.testing_utils import DummyThreadPoolExecutor, process_gtk_events


@patch("proton.vpn.app.gtk.services.refresher.certificate_refresher.run_after_seconds")
def test_enable_schedules_next_refresh_after_expiration_time(run_delayed_patch):
    api_mock = Mock()
    refresher = CertificateRefresher(
        executor=DummyThreadPoolExecutor(),
        proton_vpn_api=api_mock
    )

    api_mock.account_data\
        .vpn_credentials.pubkey_credentials.remaining_time_to_next_refresh = 0

    refresher.enable()

    run_delayed_patch.assert_called_once_with(
        refresher._refresh,
        delay_seconds=api_mock.account_data
        .vpn_credentials.pubkey_credentials.remaining_time_to_next_refresh
    )
