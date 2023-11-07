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

from proton.vpn.app.gtk.services.refresher.server_list_refresher import ServerListRefresher
from tests.unit.testing_utils import DummyThreadPoolExecutor, process_gtk_events


@patch("proton.vpn.app.gtk.services.refresher.server_list_refresher.run_after_seconds")
def test_refresh_fetches_server_list_if_expired_and_schedules_next_refresh(
        run_delayed_patch: Mock
):
    api_mock = Mock()

    # The current server list is expired.
    api_mock.server_list.expired = True

    new_server_list = Mock()
    new_server_list.seconds_until_expiration = 15 * 60
    api_mock.fetch_server_list.return_value = new_server_list

    refresher = ServerListRefresher(
        executor=DummyThreadPoolExecutor(),
        proton_vpn_api=api_mock
    )
    new_server_list_event = Event()
    refresher.connect("new-server-list", lambda *_: new_server_list_event.set())

    refresher._refresh()

    # A new server list should've been fetched.
    api_mock.fetch_server_list.assert_called_once()

    process_gtk_events()

    # The new-server-list signal should've been emitted after refreshing the server list.
    assert new_server_list_event.wait(timeout=0)

    # And the new refresh should've been scheduled after the new
    # server list/loads expire again.
    run_delayed_patch.assert_called_once_with(
        refresher._refresh,
        delay_seconds=new_server_list.seconds_until_expiration
    )


@patch("proton.vpn.app.gtk.services.refresher.server_list_refresher.run_after_seconds")
def test_refresh_updates_server_loads_if_expired_and_schedules_next_refresh(
        run_delayed_patch: Mock
):
    api_mock = Mock()

    # Only loads are expired
    api_mock.server_list.expired = False
    api_mock.server_list.loads_expired = True

    updated_server_list = Mock()
    updated_server_list.seconds_until_expiration = 60
    api_mock.update_server_loads.return_value = updated_server_list

    refresher = ServerListRefresher(
        executor=DummyThreadPoolExecutor(),
        proton_vpn_api=api_mock
    )
    new_server_loads_event = Event()
    refresher.connect("new-server-loads", lambda *_: new_server_loads_event.set())

    refresher._refresh()

    # The server list should not have been fetched...
    api_mock.fetch_server_list.assert_not_called()
    # but the loads should have been updated.
    api_mock.update_server_loads.assert_called_once()

    process_gtk_events()

    # The new-server-loads signal should've been emitted after updating the server loads.
    assert new_server_loads_event.wait(timeout=0)

    # And the next refresh should've been scheduled when the updated
    # server list expires.
    run_delayed_patch.assert_called_once_with(
        refresher._refresh,
        delay_seconds=updated_server_list.seconds_until_expiration
    )


@patch("proton.vpn.app.gtk.services.refresher.server_list_refresher.run_after_seconds")
def test_refresh_schedules_next_refresh_if_server_list_is_not_expired(
        run_delayed_patch: Mock
):
    api_mock = Mock()

    # The current server list is not expired.
    api_mock.server_list.expired = False
    api_mock.server_list.loads_expired = False
    api_mock.server_list.seconds_until_expiration = 60


    refresher = ServerListRefresher(
        executor=DummyThreadPoolExecutor(),
        proton_vpn_api=api_mock
    )

    refresher.enable()

    # The server list should not have been fetched.
    api_mock.fetch_server_list.assert_not_called()
    # The server loads should not have been fetched either.
    api_mock.update_server_loads.assert_not_called()

    process_gtk_events()

    # And the next refresh should've been scheduled when the current
    # server list expires.
    run_delayed_patch.assert_called_once_with(
        refresher._refresh,
        delay_seconds=api_mock.server_list.seconds_until_expiration
    )
