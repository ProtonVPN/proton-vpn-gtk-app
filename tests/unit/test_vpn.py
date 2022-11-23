import time
from concurrent.futures import Future
from unittest.mock import Mock
from threading import Event

import pytest

from proton.vpn.servers.list import ServerList
from proton.vpn.core_api.client_config import DEFAULT_CLIENT_CONFIG, ClientConfig
from proton.vpn.app.gtk.widgets.vpn import VPNWidget
from proton.vpn.core_api.exceptions import VPNConnectionFoundAtLogout
from proton.vpn.connection.states import Disconnected

from tests.unit.utils import process_gtk_events

PLUS_TIER = 2
FREE_TIER = 0

SERVER_LIST_TIMESTAMP = time.time()

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


@pytest.fixture
def default_client_config():
    return ClientConfig.from_dict(DEFAULT_CLIENT_CONFIG)


@pytest.fixture
def controller_mocking_successful_logout():
    controller_mock = Mock()

    logout_future = Future()
    logout_future.set_result(None)

    controller_mock.user_tier = PLUS_TIER
    controller_mock.logout.return_value = logout_future

    return controller_mock


def test_successful_logout(controller_mocking_successful_logout):
    client_config_mock = Mock()
    vpn_widget = VPNWidget(
        controller_mocking_successful_logout,
        SERVER_LIST, client_config_mock
    )
    vpn_widget.load_widget()
    process_gtk_events()
    vpn_widget.logout_button_click()

    process_gtk_events()

    controller_mocking_successful_logout.logout.assert_called_once()


@pytest.fixture
def controller_mocking_successful_logout_with_current_connection():
    controller_mock = Mock()

    logout_future_raises_exception = Future()
    logout_future_raises_exception.set_exception(VPNConnectionFoundAtLogout("test"))

    logout_future_success = Future()
    logout_future_success.set_result(None)

    controller_mock.user_tier = PLUS_TIER
    controller_mock.logout.side_effect = [logout_future_raises_exception, logout_future_success]

    return controller_mock


def test_successful_logout_with_current_connection(controller_mocking_successful_logout_with_current_connection):
    client_config_mock = Mock()
    vpn_widget = VPNWidget(
        controller_mocking_successful_logout_with_current_connection,
        SERVER_LIST, client_config_mock
    )
    vpn_widget.load_widget()
    vpn_widget.logout_button_click()

    process_gtk_events()

    controller_mocking_successful_logout_with_current_connection.logout.assert_called_once()
    assert vpn_widget._logout_dialog is not None
    vpn_widget.close_dialog(True)

    # Simulate VPN disconnection.
    vpn_widget.status_update(Disconnected())

    process_gtk_events()

    controller_mocking_successful_logout_with_current_connection.disconnect.assert_called_once()
    assert controller_mocking_successful_logout_with_current_connection.logout.call_count == 2


def test_notify_subscribers_if_client_config_was_updated(default_client_config):
    mock_controller = Mock()
    client_config_future = Future()
    client_config_future.set_result(default_client_config)
    mock_controller.get_client_config.return_value = client_config_future

    vpn_widget = VPNWidget(mock_controller)

    client_config_updated_event = Event()
    vpn_widget.connect(
        "update-client-config",
        lambda _: client_config_updated_event.set()
    )
    process_gtk_events()

    vpn_widget.retrieve_client_config()
    process_gtk_events()
    assert client_config_updated_event.wait(timeout=0) is True


def test_notify_subscribers_if_the_server_list_was_updated():
    mock_controller = Mock()
    server_list_future = Future()
    server_list_future.set_result(SERVER_LIST)
    mock_controller.get_server_list.return_value = server_list_future

    vpn_widget = VPNWidget(mock_controller)

    server_list_updated_event = Event()
    vpn_widget.connect(
        "update-server-list",
        lambda vpn_widget, server_list, : server_list_updated_event.set()
    )
    process_gtk_events()

    vpn_widget.retrieve_servers()
    process_gtk_events()
    assert server_list_updated_event.wait(timeout=0) is True

    server_list_updated_event.clear()

    vpn_widget.retrieve_servers()
    process_gtk_events()
    assert server_list_updated_event.wait(timeout=0) is not True
