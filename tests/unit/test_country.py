import time
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import Mock

import pytest

from proton.vpn.connection.states import ConnectionStateEnum, Connecting, Connected, Disconnected
from proton.vpn.servers import ServerList, Country

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
def country(country_servers):
    return Country(code=COUNTRY_CODE, servers=country_servers)


@pytest.fixture
def mock_controller():
    return Mock(Controller)


def test_country_row_toggles_servers_when_requested(
        country, mock_controller
):
    mock_controller.user_tier = PLUS_TIER
    country_row = CountryRow(country=country,controller=mock_controller)

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
        country, mock_controller
):
    mock_controller.user_tier = FREE_TIER
    country_row = CountryRow(country=country, controller=mock_controller)

    assert country_row.upgrade_required


@pytest.mark.parametrize(
    "connection_state", [(Connecting()), (Connected()), (Disconnected())]
)
def test_country_row_updates_server_rows_on_connection_status_update(
        connection_state, country, mock_controller
):
    mock_controller.user_tier = PLUS_TIER
    country_row = CountryRow(country=country, controller=mock_controller)

    vpn_server = Mock()
    vpn_server.servername = country.servers[0].name

    country_row.connection_status_update(connection_state, vpn_server)

    process_gtk_events()

    assert country_row.connection_state == connection_state.state
    assert country_row.server_rows[0].connection_state == connection_state.state


def test_connect_button_click_triggers_vpn_connection_to_country(country):
    mock_api = Mock()
    mock_logical_server = Mock()
    mock_vpn_server = Mock()
    mock_api.get_user_tier.return_value = PLUS_TIER
    mock_api.servers.get_server_by_country_code.return_value = mock_logical_server
    mock_api.get_vpn_server.return_value = mock_vpn_server

    with ThreadPoolExecutor() as thread_pool_executor:
        controller = Controller(thread_pool_executor, mock_api, 0)

        country_row = CountryRow(country=country, controller=controller)

        country_row.click_connect_button()

        process_gtk_events()

        # Assert that the country code was used to retrieve the VPN server.
        mock_api.servers.get_server_by_country_code.assert_called_once_with(
            country.code
        )
        # Assert that the connection was done using the VPN server above.
        mock_api.connection.connect.assert_called_once_with(
            mock_vpn_server, protocol="openvpn-udp"
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
    mock_controller.user_tier = PLUS_TIER

    country_row = CountryRow(
        country=country,
        controller=mock_controller,
        connected_server_name=country.servers[1].name
    )

    assert country_row.connection_state == ConnectionStateEnum.CONNECTED
    assert country_row.server_rows[1].connection_state == ConnectionStateEnum.CONNECTED


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
    mock_controller.user_tier = PLUS_TIER

    country_row = CountryRow(
        country=country,
        controller=mock_controller,
        show_country_servers=True  # Country servers should
    )

    assert country_row.showing_servers

@pytest.fixture
def free_and_plus_servers():
    return ServerList(apidata={
        "LogicalServers": [
            {
                "ID": 1,
                "Name": "JP#9",
                "Status": 1,
                "Servers": [{"Status": 1}],
                "ExitCountry": "JP",
                "Tier": PLUS_TIER,

            },
            {
                "ID": 2,
                "Name": "JP-FREE#10",
                "Status": 1,
                "Servers": [{"Status": 1}],
                "ExitCountry": "JP",
                "Tier": FREE_TIER,

            },
        ]
    })


@pytest.mark.parametrize("user_tier", [FREE_TIER, PLUS_TIER])
def test_country_widget_shows_user_tier_servers_first(
        user_tier, free_and_plus_servers, mock_controller
):
    """
    Free users should have free servers listed first.
    Plus users should have plus servers listed first.
    """
    mock_controller.user_tier = user_tier

    country = Country(code="jp", servers=free_and_plus_servers)

    country_row = CountryRow(
        country=country,
        controller=mock_controller
    )

    assert len(country_row.server_rows) == 2
    assert country_row.server_rows[0].server_tier == user_tier
