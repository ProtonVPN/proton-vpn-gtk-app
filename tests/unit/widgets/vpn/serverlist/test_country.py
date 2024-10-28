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
import time
from unittest.mock import Mock

import pytest

from proton.vpn.connection.states import ConnectionStateEnum, Connecting, Connected, Disconnected
from proton.vpn.session.servers import ServerList, Country, LogicalServer

from proton.vpn.app.gtk.controller import Controller
from proton.vpn.app.gtk.widgets.vpn.serverlist.country import ImmediateCountryRow
from proton.vpn.app.gtk.widgets.vpn.serverlist.icons import UnderMaintenanceIcon
from tests.unit.testing_utils import process_gtk_events
from proton.vpn.logging import logging


FREE_TIER = 0
PLUS_TIER = 2
COUNTRY_CODE = "AR"


@pytest.fixture
def country_servers():
    api_data = {
        "LogicalServers": [
            {
                "ID": 1,
                "Name": "AR#1",
                "Status": 1,
                "Load": 50,
                "Servers": [{"Status": 1}],
                "ExitCountry": COUNTRY_CODE,
                "Tier": 1,
            },
            {
                "ID": 2,
                "Name": "AR#2",
                "Status": 1,
                "Load": 50,
                "Servers": [{"Status": 1}],
                "ExitCountry": COUNTRY_CODE,
                "Tier": 2,
            },
        ]
    }
    return ServerList(
        user_tier=PLUS_TIER,
        logicals=[LogicalServer(server) for server in api_data["LogicalServers"]]
    )


@pytest.fixture
def country(country_servers):
    return Country(code=COUNTRY_CODE, servers=country_servers)


@pytest.fixture
def mock_controller():
    return Mock(Controller)


def test_country_row_toggles_servers_when_requested(
        country, mock_controller
):
    country_row = ImmediateCountryRow(country=country, user_tier=PLUS_TIER, controller=mock_controller)

    # Initially the servers should not be shown
    assert not country_row.showing_servers

    showing_servers_expected = True
    for _ in country.servers:
        country_row.click_toggle_country_servers_button()

        process_gtk_events()

        # assert that the servers were toggled
        assert country_row.showing_servers is showing_servers_expected

        showing_servers_expected = not showing_servers_expected


def test_country_row_shows_upgrade_link_when_country_servers_are_not_in_the_users_plan(
        country, mock_controller
):
    country_row = ImmediateCountryRow(country=country, user_tier=FREE_TIER, controller=mock_controller)

    assert country_row.upgrade_required


@pytest.mark.parametrize(
    "connection_state", [(Connecting()), (Connected()), (Disconnected())]
)
def test_country_row_updates_server_rows_on_connection_status_update(
        connection_state, country, mock_controller
):
    country_row = ImmediateCountryRow(country=country, user_tier=PLUS_TIER, controller=mock_controller)

    connection_state = Mock()
    connection_state.context.connection.server_id = country.servers[0].id

    country_row.connection_status_update(connection_state)

    process_gtk_events()

    assert country_row.connection_state == connection_state.type
    assert country_row.server_rows[0].connection_state == connection_state.type


def test_connect_button_click_triggers_vpn_connection_to_country(country, mock_controller):
    country_row = ImmediateCountryRow(country=country, user_tier=PLUS_TIER, controller=mock_controller)

    country_row.click_connect_button()

    process_gtk_events()

    mock_controller.connect_to_country.assert_called_once_with(
        country.code
    )


def test_initialize_currently_connected_country(
        country, mock_controller
):
    """
    When reloading the server list, all country rows are recreated.
    When recreating the country row containing the server the user is
    currently connected to, we need to initialize both the new country row
    and its child server row in a "connected" state.
    """
    country_row = ImmediateCountryRow(
        country=country,
        user_tier=PLUS_TIER,
        controller=mock_controller,
        connected_server_id=country.servers[1].id
    )

    assert country_row.connection_state == ConnectionStateEnum.CONNECTED
    assert country_row.server_rows[1].connection_state == ConnectionStateEnum.CONNECTED


@pytest.fixture
def country_with_server_under_maintenance():
    api_data = {
        "LogicalServers": [
            {
                "ID": 1,
                "Name": "AR#3",
                "Status": 0,
                "Load": 0,
                "Servers": [{"Status": 0}],
                "ExitCountry": COUNTRY_CODE,
                "Tier": 1,
            },
        ]
    }
    logicals=[LogicalServer(server) for server in api_data["LogicalServers"]]
    return Country(
        code=COUNTRY_CODE,
        servers=ServerList(user_tier=PLUS_TIER, logicals=logicals)
    )


def test_initialize_currently_connected_server_when_server_is_flagged_for_maintenance_a_warning_is_logged(
        country_with_server_under_maintenance, mock_controller, caplog
):
    """
    When reloading the server list, all country rows are recreated.
    If a user is connected to a server that was flagged as under maintenance,
    we need to ensure that the button for that server is disabled, and replaced
    by a label displaying that the server is under maintenance.
    """
    caplog.set_level(logging.WARNING)
    ImmediateCountryRow(
        country=country_with_server_under_maintenance,
        user_tier=PLUS_TIER,
        controller=mock_controller,
        connected_server_id=country_with_server_under_maintenance.servers[0].id
    )
    for record in caplog.records:
        assert record.levelname == "WARNING"


def test_initialize_country_row_showing_country_servers(
        country,  mock_controller
):
    """
    When reloading the server list, all country rows are recreated.
    By default, country rows are shown collapsed (i.e. hiding all country
    servers). However, if a country row is expanded (i.e. showing all country
    servers) when reloading the server list, then it needs to be recreated in
    the expanded state. This is what we test here.
    """
    country_row = ImmediateCountryRow(
        country=country,
        user_tier=PLUS_TIER,
        controller=mock_controller,
        show_country_servers=True  # Country servers should
    )

    assert country_row.showing_servers


@pytest.fixture
def free_and_plus_servers():
    api_response = {
        "LogicalServers": [
            {
                "ID": 1,
                "Name": "JP#9",
                "Status": 1,
                "Load": 50,
                "Servers": [{"Status": 1}],
                "ExitCountry": "JP",
                "Tier": PLUS_TIER,

            },
            {
                "ID": 2,
                "Name": "JP-FREE#10",
                "Status": 1,
                "Load": 50,
                "Servers": [{"Status": 1}],
                "ExitCountry": "JP",
                "Tier": FREE_TIER,

            },
        ]
    }
    return [LogicalServer(server) for server in api_response["LogicalServers"]]


@pytest.mark.parametrize("user_tier", [FREE_TIER, PLUS_TIER])
def test_country_widget_shows_user_tier_servers_first(
        user_tier, free_and_plus_servers, mock_controller
):
    """
    Free users should have free servers listed first.
    Plus users should have plus servers listed first.
    """
    servers = ServerList(user_tier=user_tier, logicals=free_and_plus_servers)
    country = Country(code="jp", servers=free_and_plus_servers)

    country_row = ImmediateCountryRow(
        country=country,
        user_tier=user_tier,
        controller=mock_controller
    )

    assert len(country_row.server_rows) == 2
    assert country_row.server_rows[0].server_tier == user_tier
