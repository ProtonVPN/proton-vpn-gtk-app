import time
from unittest.mock import Mock

import pytest

from proton.vpn.connection.states import ConnectionStateEnum, Connecting, Connected, Disconnected
from proton.vpn.servers import ServerList, Country

from proton.vpn.app.gtk.controller import Controller
from proton.vpn.app.gtk.widgets.vpn.serverlist.country import CountryRow
from tests.unit.utils import process_gtk_events
from proton.vpn.logging import logging
from proton.vpn.servers.enums import ServerFeatureEnum


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
    country_row = CountryRow(country=country, user_tier=PLUS_TIER, controller=mock_controller)

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
    country_row = CountryRow(country=country, user_tier=FREE_TIER, controller=mock_controller)

    assert country_row.upgrade_required


@pytest.mark.parametrize(
    "connection_state", [(Connecting()), (Connected()), (Disconnected())]
)
def test_country_row_updates_server_rows_on_connection_status_update(
        connection_state, country, mock_controller
):
    country_row = CountryRow(country=country, user_tier=PLUS_TIER, controller=mock_controller)

    connection_state = Mock()
    connection_state.context.connection.server_id = country.servers[0].id

    country_row.connection_status_update(connection_state)

    process_gtk_events()

    assert country_row.connection_state == connection_state.state
    assert country_row.server_rows[0].connection_state == connection_state.state


def test_connect_button_click_triggers_vpn_connection_to_country(country, mock_controller):
    country_row = CountryRow(country=country, user_tier=PLUS_TIER, controller=mock_controller)

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
    country_row = CountryRow(
        country=country,
        user_tier=PLUS_TIER,
        controller=mock_controller,
        connected_server_id=country.servers[1].id
    )

    assert country_row.connection_state == ConnectionStateEnum.CONNECTED
    assert country_row.server_rows[1].connection_state == ConnectionStateEnum.CONNECTED


@pytest.fixture
def country_with_server_under_maintenance():
    return Country(code=COUNTRY_CODE, servers=ServerList(apidata={
        "LogicalServers": [
            {
                "ID": 1,
                "Name": "AR#3",
                "Status": 0,
                "Servers": [{"Status": 0}],
                "ExitCountry": COUNTRY_CODE,
                "Tier": 1,
            },
        ],
        "LogicalsUpdateTimestamp": time.time(),
        "LoadsUpdateTimestamp": time.time()
    }))


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
    country_row = CountryRow(
        country=country_with_server_under_maintenance,
        user_tier=PLUS_TIER,
        controller=mock_controller,
        connected_server_id=country_with_server_under_maintenance.servers[0].id
    )
    for record in caplog.records:
        assert record.levelname == "WARNING"


def test_initialize_currently_connected_server_when_server_is_flagged_for_maintenance_where_button_is_hidden_and_label_is_displayed(
        country_with_server_under_maintenance, mock_controller, caplog
):
    """
    When reloading the server list, all country rows are recreated.
    If a user is connected to a server that was flagged as under maintenance,
    we need to ensure that the button for that server is disabled, and replaced
    by a label displaying that the server is under maintenance.
    """
    caplog.set_level(logging.WARNING)
    country_row = CountryRow(
        country=country_with_server_under_maintenance,
        user_tier=PLUS_TIER,
        controller=mock_controller,
        connected_server_id=country_with_server_under_maintenance.servers[0].id
    )

    assert not country_row.server_rows[0].is_connect_button_visible
    assert country_row.server_rows[0].is_under_maintenance_label_visible


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
    country_row = CountryRow(
        country=country,
        user_tier=PLUS_TIER,
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
    country = Country(code="jp", servers=free_and_plus_servers)

    country_row = CountryRow(
        country=country,
        user_tier=user_tier,
        controller=mock_controller
    )

    assert len(country_row.server_rows) == 2
    assert country_row.server_rows[0].server_tier == user_tier


@pytest.fixture
def country_servers_with_secure_core():
    return ServerList(apidata={
        "LogicalServers": [
            {
                "ID": 1,
                "Name": "AR#1",
                "Status": 1,
                "Servers": [{"Status": 1}],
                "ExitCountry": COUNTRY_CODE,
                "Features": 8,
                "Tier": 1,
            },
            {
                "ID": 2,
                "Name": "AR#2",
                "Status": 1,
                "Servers": [{"Status": 1}],
                "ExitCountry": COUNTRY_CODE,
                "Features": 1,
                "Tier": 2,
            },
        ],
        "LogicalsUpdateTimestamp": time.time(),
        "LoadsUpdateTimestamp": time.time()
    })


def test_assert_country_widget_only_contains_non_secure_core_servers(
    country_servers_with_secure_core, mock_controller
):
    country_row = CountryRow(
        country=Country(code=COUNTRY_CODE, servers=country_servers_with_secure_core),
        user_tier=PLUS_TIER,
        controller=mock_controller,
    )

    assert len(country_row.server_rows) == 1
    assert country_row.server_rows[0].server_label == "AR#1"
