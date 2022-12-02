import time
from concurrent.futures import Future
from unittest.mock import Mock

import pytest
from proton.vpn.servers.list import ServerList
from proton.vpn.connection.states import Connecting, Connected, Disconnected

from proton.vpn.app.gtk.widgets.vpn.server_list import ServerListWidget
from tests.unit.utils import process_gtk_events


PLUS_TIER = 2
FREE_TIER = 0

SERVER_LIST_TIMESTAMP = time.time()


@pytest.fixture
def unsorted_server_list():
    return ServerList(apidata={
        "LogicalServers": [
            {
                "ID": 2,
                "Name": "AR#10",
                "Status": 1,
                "Servers": [{"Status": 1}],
                "ExitCountry": "AR",
                "Tier": PLUS_TIER,
            },
            {
                "ID": 1,
                "Name": "JP-FREE#10",
                "Status": 1,
                "Servers": [{"Status": 1}],
                "ExitCountry": "JP",
                "Tier": FREE_TIER,

            },
            {
                "ID": 3,
                "Name": "AR#9",
                "Status": 1,
                "Servers": [{"Status": 1}],
                "ExitCountry": "AR",
                "Tier": PLUS_TIER,
            },
            {
                "ID": 5,
                "Name": "CH-JP#1",
                "Status": 1,
                "Servers": [{"Status": 1}],
                "Features": 1,  # Secure core feature
                "ExitCountry": "JP",
                "Tier": PLUS_TIER,
            },
            {
                "ID": 4,
                "Name": "JP#9",
                "Status": 1,
                "Servers": [{"Status": 1}],
                "ExitCountry": "JP",
                "Tier": PLUS_TIER,

            },
        ],
        "LogicalsUpdateTimestamp": SERVER_LIST_TIMESTAMP,
        "LoadsUpdateTimestamp": SERVER_LIST_TIMESTAMP
    })


SERVER_LIST = ServerList(apidata={
    "LogicalServers": [
        {
            "ID": 1,
            "Name": "AR#1",
            "Status": 1,
            "Servers": [{"Status": 1}],
            "ExitCountry": "AR",
            "Tier": PLUS_TIER,
        },
        {
            "ID": 2,
            "Name": "AR#2",
            "Status": 1,
            "Servers": [{"Status": 1}],
            "ExitCountry": "AR",
            "Tier": PLUS_TIER,
        },
    ],
    "LogicalsUpdateTimestamp": SERVER_LIST_TIMESTAMP,
    "LoadsUpdateTimestamp": SERVER_LIST_TIMESTAMP
})


SERVER_LIST_UPDATED = ServerList(apidata={
    "LogicalServers": [
        {
            "ID": 1,
            "Name": "Server Name Updated",
            "Status": 1,
            "Servers": [{"Status": 1}],
            "ExitCountry": "AR",
            "Tier": PLUS_TIER,

        },
    ],
    "LogicalsUpdateTimestamp": SERVER_LIST_TIMESTAMP + 1,
    "LoadsUpdateTimestamp": SERVER_LIST_TIMESTAMP + 1
})


@pytest.mark.parametrize(
    "user_tier,expected_country_names", [
        (FREE_TIER, ["Japan", "Argentina"]),
        (PLUS_TIER, ["Argentina", "Japan"])
    ]
)
def test_server_widget_orders_country_rows_depening_on_user_tier(
        user_tier, expected_country_names, unsorted_server_list
):
    """
    Plus users should see countries sorted alphabetically.
    Free users, apart from having countries sorted alphabetically, should see
    countries having free servers first.
    """
    mock_controller = Mock()
    print(user_tier)
    mock_controller.user_tier = user_tier

    servers_widget = ServerListWidget(
        controller=mock_controller,
        server_list=unsorted_server_list
    )
    country_names = [country_row.country_name for country_row in servers_widget.country_rows]
    assert country_names == expected_country_names


@pytest.mark.parametrize(
    "connection_state", [
        Connecting(),
        Connected(),
        Disconnected()
    ]
)
def test_server_widget_updates_country_rows_on_connection_status_update(
        connection_state
):
    connection_mock = Mock()
    connection_mock.server_name = SERVER_LIST[0].name
    connection_state.context.connection = connection_mock

    controller_mock = Mock()
    controller_mock.user_tier = PLUS_TIER
    servers_widget = ServerListWidget(
        controller=controller_mock,
        server_list=SERVER_LIST
    )
    servers_widget.connection_status_update(connection_state)
    process_gtk_events()
    assert servers_widget.country_rows[0].connection_state == connection_state.state
