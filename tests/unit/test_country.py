import time
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import Mock

import pytest

from proton.vpn.connection.states import ConnectionStateEnum, Connecting, Connected, Disconnected
from proton.vpn.servers.list import ServerList

from proton.vpn.app.gtk.controller import Controller
from proton.vpn.app.gtk.widgets.vpn.country import CountryRow
from tests.unit.utils import process_gtk_events

FREE_TIER = 0
PLUS_TIER = 2
COUNTRY_CODE = "AR"

@pytest.fixture
def country_servers():
    return ServerList(apidata={
        "LogicalServers": [
            {
                "ID": 1,
                "Name": "AR#1",
                "Status": 1,
                "Servers": [{"Status": 1}],
                "ExitCountry": COUNTRY_CODE,
                "Tier": 1,
            },
            {
                "ID": 2,
                "Name": "AR#2",
                "Status": 1,
                "Servers": [{"Status": 1}],
                "ExitCountry": COUNTRY_CODE,
                "Tier": 2,
            },
        ],
        "LogicalsUpdateTimestamp": time.time(),
        "LoadsUpdateTimestamp": time.time()
    })


@pytest.fixture
def mock_controller():
    return Mock(Controller)


def test_country_row_toggles_servers_when_requested(
        country_servers, mock_controller
):
    mock_controller.user_tier = PLUS_TIER
    country_row = CountryRow(
        country_code=COUNTRY_CODE,
        country_servers=country_servers,
        controller=mock_controller
    )

    # Initially the servers should not be shown
    assert not country_row.showing_servers

    showing_servers_expected = True
    for _ in range(2):
        country_row.click_toggle_country_servers_button()

        process_gtk_events()

        # assert that the servers were toggled
        assert country_row.showing_servers is showing_servers_expected

        showing_servers_expected = not showing_servers_expected


def test_country_row_shows_upgrade_link_when_country_servers_are_not_in_the_users_plan(
        country_servers, mock_controller
):
    mock_controller.user_tier = FREE_TIER
    country_row = CountryRow(
        country_servers=country_servers, country_code=COUNTRY_CODE, controller=mock_controller
    )

    assert country_row.upgrade_required


@pytest.mark.parametrize(
    "connection_state", [(Connecting()), (Connected()), (Disconnected())]
)
def test_country_row_updates_server_rows_on_connection_status_update(
        connection_state, country_servers, mock_controller
):
    mock_controller.user_tier = PLUS_TIER
    country_row = CountryRow(
        country_servers=country_servers, country_code=COUNTRY_CODE, controller=mock_controller
    )

    vpn_server = Mock()
    vpn_server.servername = country_servers[0].name

    country_row.connection_status_update(connection_state, vpn_server)

    process_gtk_events()

    assert country_row.connection_state == connection_state.state
    assert country_row.server_rows[0].connection_state == connection_state.state


def test_connect_button_click_triggers_vpn_connection_to_country(
        country_servers
):
    mock_api = Mock()
    mock_api.get_user_tier.return_value = PLUS_TIER
    mock_vpn_server = Mock()
    mock_api.servers.get_server_by_country_code.return_value = mock_vpn_server

    with ThreadPoolExecutor() as thread_pool_executor:
        controller = Controller(thread_pool_executor, mock_api, 0)

        country_row = CountryRow(
            country_servers=country_servers,
            controller=controller,
            country_code=COUNTRY_CODE
        )

        country_row.click_connect_button()

        process_gtk_events()

        # Assert that the country code was used to retrieve the VPN server.
        mock_api.servers.get_server_by_country_code.assert_called_once_with(
            COUNTRY_CODE
        )
        # Assert that the connection was done using the VPN server above.
        mock_api.connection.connect.assert_called_once_with(
            mock_vpn_server, protocol="openvpn-udp"
        )


def test_initialize_currently_connected_country(
        country_servers, mock_controller
):
    mock_controller.user_tier = PLUS_TIER
    connected_country_row = Mock()
    connected_country_row.country_code = COUNTRY_CODE
    connected_country_row.connected_server_row.server.name = country_servers[1].name
    country_row = CountryRow(
        country_servers=country_servers,
        controller=mock_controller,
        country_code=COUNTRY_CODE,
        connected_country_row=connected_country_row
    )

    assert country_row.connection_state == ConnectionStateEnum.CONNECTED
    assert country_row.server_rows[1].connection_state == ConnectionStateEnum.CONNECTED
