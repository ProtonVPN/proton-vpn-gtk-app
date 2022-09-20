import time
from concurrent.futures import Future
from threading import Event
from unittest.mock import Mock

import pytest
from proton.vpn.servers.list import ServerList
from proton.vpn.servers.server_types import LogicalServer
from proton.vpn.connection.states import Connecting, Connected, Disconnected

from proton.vpn.app.gtk.widgets.servers import ServersWidget, ServerRow, CountryHeader, CountryRow
from tests.unit.utils import process_gtk_events


SERVER_LIST_TIMESTAMP = time.time()

UNSORTED_SERVER_LIST = ServerList(apidata={
    "LogicalServers": [
        {
            "ID": 2,
            "Name": "IS#10",
            "Status": 1,
            "Servers": [{"Status": 1}],
            "ExitCountry": "IS",

        },
        {
            "ID": 1,
            "Name": "Random Name",
            "Status": 1,
            "Servers": [{"Status": 1}],
            "ExitCountry": "JP",

        },
        {
            "ID": 3,
            "Name": "IS#9",
            "Status": 1,
            "Servers": [{"Status": 1}],
            "ExitCountry": "IS",
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
        },
        {
            "ID": 2,
            "Name": "AR#2",
            "Status": 1,
            "Servers": [{"Status": 1}],
            "ExitCountry": "AR",
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

            },
        ],
        "LogicalsUpdateTimestamp": SERVER_LIST_TIMESTAMP + 1,
        "LoadsUpdateTimestamp": SERVER_LIST_TIMESTAMP + 1
    })


def test_retrieve_servers_shows_servers_grouped_by_country_and_sorted_alphabetically():
    future_server_list = Future()
    future_server_list.set_result(UNSORTED_SERVER_LIST)
    mock_controller = Mock()
    mock_controller.get_server_list.return_value = future_server_list

    servers_widget = ServersWidget(controller=mock_controller)

    server_list_updated_event = Event()
    servers_widget.connect(
        "server-list-updated",
        lambda _: server_list_updated_event.set()
    )

    servers_widget.retrieve_servers()

    process_gtk_events()

    server_list_updated = server_list_updated_event.wait(timeout=0)
    assert server_list_updated

    assert len(servers_widget.country_rows) == 2

    assert servers_widget.country_rows[0].country_name == "Iceland"
    assert servers_widget.country_rows[0].server_rows[0].server.name == "IS#9"
    assert servers_widget.country_rows[0].server_rows[1].server.name == "IS#10"
    assert servers_widget.country_rows[1].country_name == "Japan"
    assert servers_widget.country_rows[1].server_rows[0].server.name == "Random Name"


@pytest.mark.parametrize(
    "server_list_1,first_ui_update_expected,server_list_2,second_ui_update_expected",
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

    servers_widget = ServersWidget(controller=mock_controller)

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


def test_server_row_displays_server_name():
    server = LogicalServer(data={
            "Name": "IS#1",
            "Status": 1,
            "Servers": [
                {
                    "ID": "OYB-3pMQQA2Z2Qnp5s5nIvTV…x9DCAUM9uXfM2ZUFjzPXw==",
                    "Status": 1
                }
            ]
    })

    server_row = ServerRow(server)

    assert server_row.server_label == "IS#1"


def test_server_row_signals_server_under_maintenance():
    server = LogicalServer(data={
        "Name": "IS#1",
        "Status": 0
    })

    server_row = ServerRow(server)

    assert server_row.under_maintenance


def test_server_connect_button_triggers_vpn_connection():
    mock_controller = Mock()
    servers_widget = ServersWidget(
        controller=mock_controller, server_list=SERVER_LIST
    )

    servers_widget.country_rows[0].server_rows[0].click_connect_button()

    mock_controller.connect.assert_called_once_with(server_name=SERVER_LIST[0].name)


@pytest.mark.parametrize(
    "connection_state",[(Connecting()), (Connected()), (Disconnected()) ]
)
def test_server_widget_updates_row_according_to_connection_status_update(connection_state):
    mock_controller = Mock()
    servers_widget = ServersWidget(
        controller=mock_controller, server_list=SERVER_LIST
    )
    vpn_server = Mock()
    vpn_server.servername = SERVER_LIST[0].name

    servers_widget.connection_status_update(connection_state, vpn_server)

    process_gtk_events()

    assert servers_widget.country_rows[0].server_rows[0].connection_state == connection_state.state


def test_country_row_toggles_servers_when_requested():
    country_row = CountryRow(
        country_code="AR",
        country_servers=SERVER_LIST
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
