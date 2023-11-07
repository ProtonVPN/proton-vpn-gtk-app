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

from proton.vpn.app.gtk.services.refresher.client_config_refresher import ClientConfigRefresher
from tests.unit.testing_utils import DummyThreadPoolExecutor, process_gtk_events


@patch("proton.vpn.app.gtk.services.refresher.client_config_refresher.run_after_seconds")
def test_enable_schedules_next_refresh_after_expiration_time(run_delayed_patch):
    api_mock = Mock()
    refresher = ClientConfigRefresher(
        executor=DummyThreadPoolExecutor(),
        proton_vpn_api=api_mock
    )

    api_mock.client_config.seconds_until_expiration = 0

    refresher.enable()

    run_delayed_patch.assert_called_once_with(
        refresher._refresh,
        delay_seconds=api_mock.client_config.seconds_until_expiration
    )


@patch("proton.vpn.app.gtk.services.refresher.client_config_refresher.run_after_seconds")
def test_refresh_fetches_client_config_and_schedules_another_refresh_after_new_client_config_expiration_time(
        run_delayed_patch
):
    api_mock = Mock()
    refresher = ClientConfigRefresher(
        executor=DummyThreadPoolExecutor(),
        proton_vpn_api=api_mock
    )
    new_client_config_event = Event()
    refresher.connect("new-client-config", lambda *_: new_client_config_event.set())

    new_client_config = Mock()
    new_client_config.seconds_until_expiration = 60
    api_mock.fetch_client_config.return_value = new_client_config

    refresher._refresh()

    process_gtk_events()

    # The new-client-config signal should've been emitted.
    assert new_client_config_event.wait(timeout=0)

    api_mock.fetch_client_config.assert_called_once()

    run_delayed_patch.assert_called_once_with(
        refresher._refresh,
        delay_seconds=new_client_config.seconds_until_expiration
    )
