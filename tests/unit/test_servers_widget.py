import time
from concurrent.futures import Future
from threading import Event
from unittest.mock import Mock

import pytest
from proton.vpn.servers.list import ServerList
from proton.vpn.servers.server_types import LogicalServer

from proton.vpn.app.gtk.widgets.servers import ServersWidget, ServerRow
from tests.unit.utils import process_gtk_events


SERVER_LIST_TIMESTAMP = time.time()

UNSORTED_SERVER_LIST = ServerList(apidata={
    "LogicalServers": [
        {
            "ID": 1,
            "Name": "Random Name",
            "Status": 1,
            "Servers": [{"Status": 1}]

        },
        {
            "ID": 2,
            "Name": "IS#10",
            "Status": 1,
            "Servers": [{"Status": 1}]

        },
        {
            "ID": 3,
            "Name": "IS#9",
            "Status": 1,
            "Servers": [{"Status": 1}]
        },
    ],
    "LogicalsUpdateTimestamp": SERVER_LIST_TIMESTAMP
})


SERVER_LIST = ServerList(apidata={
    "LogicalServers": [
        {
            "ID": 1,
            "Name": "Server Name 1",
            "Status": 1,
            "Servers": [{"Status": 1}]
        },
        {
            "ID": 2,
            "Name": "Server Name 2",
            "Status": 1,
            "Servers": [{"Status": 1}]
        },
    ],
    "LogicalsUpdateTimestamp": SERVER_LIST_TIMESTAMP
})


SERVER_LIST_UPDATED = ServerList(apidata={
        "LogicalServers": [
            {
                "ID": 1,
                "Name": "Server Name Updated",
                "Status": 1,
                "Servers": [{"Status": 1}]

            },
        ],
        "LogicalsUpdateTimestamp": SERVER_LIST_TIMESTAMP + 1
    })


def test_retrieve_servers_shows_server_sorted():
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

    assert len(servers_widget.server_rows) == 3
    assert servers_widget.server_rows[0].server_label == "IS#9"
    assert servers_widget.server_rows[1].server_label == "IS#10"
    assert servers_widget.server_rows[2].server_label == "Random Name"


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
        assert servers_widget.server_rows[0].server_label == server_list[0].name

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

    assert server_row.server_label == "IS#1 (under maintenance)"
