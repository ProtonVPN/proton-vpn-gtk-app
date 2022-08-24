from concurrent.futures import Future
from threading import Event
from unittest.mock import Mock

from proton.vpn.servers.server_types import LogicalServer

from proton.vpn.app.gtk.widgets.servers import ServersWidget, ServerRow
from tests.unit.utils import process_gtk_events


def test_retrieve_servers():
    server_list = [
        LogicalServer(data={
            "Name": "Random Name",
            "Status": 1,
            "Servers": [{"Status": 1}]

        }),
        LogicalServer(data={
            "Name": "IS#10",
            "Status": 1,
            "Servers": [{"Status": 1}]

        }),
        LogicalServer(data={
            "Name": "IS#9",
            "Status": 1,
            "Servers": [{"Status": 1}]
        }),
    ]
    future_server_list = Future()
    future_server_list.set_result(server_list)
    mock_controller = Mock()
    mock_controller.get_server_list.return_value = future_server_list

    servers_widget = ServersWidget(controller=mock_controller)

    server_list_ready_event = Event()
    servers_widget.connect(
        "server_list_ready",
        lambda _: server_list_ready_event.set()
    )

    servers_widget.retrieve_servers()

    process_gtk_events()

    server_list_ready = server_list_ready_event.wait(timeout=0)
    assert server_list_ready

    assert len(servers_widget.server_rows) == 3
    assert servers_widget.server_rows[0].server_label == "IS#9"
    assert servers_widget.server_rows[1].server_label == "IS#10"
    assert servers_widget.server_rows[2].server_label == "Random Name"


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
