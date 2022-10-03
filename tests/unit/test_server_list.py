import time
from concurrent.futures import Future
from threading import Event
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
    future_server_list = Future()
    future_server_list.set_result(unsorted_server_list)
    mock_controller = Mock()
    mock_controller.get_server_list.return_value = future_server_list
    print(user_tier)
    mock_controller.user_tier = user_tier

    servers_widget = ServerListWidget(controller=mock_controller)

    server_list_updated_event = Event()
    servers_widget.connect(
        "server-list-updated",
        lambda _: server_list_updated_event.set()
    )

    servers_widget.retrieve_servers()

    process_gtk_events()

    server_list_updated = server_list_updated_event.wait(timeout=0)
    assert server_list_updated

    country_names = [country_row.country_name for country_row in servers_widget.country_rows]
    assert country_names == expected_country_names


@pytest.mark.parametrize(
    "server_list_1, first_ui_update_expected, server_list_2, second_ui_update_expected",
    [
        (SERVER_LIST, True, SERVER_LIST, False),
        (SERVER_LIST, True, SERVER_LIST_UPDATED, True)
    ])
def test_retrieve_servers_only_triggers_a_ui_update_if_the_server_list_was_updated(
        server_list_1, first_ui_update_expected,
        server_list_2, second_ui_update_expected
):
    future_server_lists = []
    for server_list in [server_list_1, server_list_2]:
        future_server_list = Future()
        future_server_list.set_result(server_list)
        future_server_lists.append(future_server_list)

    mock_controller = Mock()
    mock_controller.get_server_list.side_effect = future_server_lists
    mock_controller.user_tier = PLUS_TIER

    servers_widget = ServerListWidget(controller=mock_controller)

    server_list_updated_event = Event()
    servers_widget.connect(
        "server-list-updated",
        lambda _: server_list_updated_event.set()
    )

    for expected_server_list_update, server_list in zip(
        [first_ui_update_expected, second_ui_update_expected],
        [server_list_1, server_list_2]
    ):
        servers_widget.retrieve_servers()
        process_gtk_events()
        server_list_updated = server_list_updated_event.wait(timeout=0)

        assert server_list_updated == expected_server_list_update
        first_server = servers_widget.country_rows[0].server_rows[0]
        assert first_server.server_label == server_list[0].name

        server_list_updated_event.clear()


@pytest.mark.parametrize(
    "connection_state", [(Connecting()), (Connected()), (Disconnected())]
)
def test_server_widget_updates_country_rows_on_connection_status_update(
        connection_state
):
    controller_mock = Mock()
    controller_mock.user_tier = PLUS_TIER
    servers_widget = ServerListWidget(
        controller=controller_mock, server_list=SERVER_LIST
    )
    vpn_server = Mock()
    vpn_server.servername = SERVER_LIST[0].name

    servers_widget.connection_status_update(connection_state, vpn_server)

    process_gtk_events()

    assert servers_widget.country_rows[0].connection_state == connection_state.state

