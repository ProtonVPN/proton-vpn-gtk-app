from concurrent.futures import Future
from unittest.mock import Mock
from concurrent.futures import ThreadPoolExecutor

import pytest

from proton.vpn.app.gtk.widgets.vpn.vpn import VPNWidget, QuickConnectWidget
from proton.vpn.core_api.exceptions import VPNConnectionFoundAtLogout
from proton.vpn.connection.states import Disconnected, Connected
from proton.vpn.app.gtk.controller import Controller

from tests.unit.utils import process_gtk_events


@pytest.fixture
def controller_mocking_successful_logout():
    controller_mock = Mock()

    logout_future = Future()
    logout_future.set_result(None)

    controller_mock.logout.return_value = logout_future

    return controller_mock


def test_successful_logout(controller_mocking_successful_logout):
    vpn_widget = VPNWidget(controller_mocking_successful_logout)
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

    controller_mock.logout.side_effect = [logout_future_raises_exception, logout_future_success]

    return controller_mock


def test_successful_logout_with_current_connection(controller_mocking_successful_logout_with_current_connection):
    vpn_widget = VPNWidget(controller_mocking_successful_logout_with_current_connection)
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


@pytest.mark.parametrize(
    "connection_state", [(Connected()), (Disconnected())]
)
def test_quick_connect_widget_updates_state_according_to_connection_status_update(connection_state):
    mock_controller = Mock()
    quick_connect_widget = QuickConnectWidget(controller=mock_controller)

    quick_connect_widget.connection_status_update(connection_state)

    process_gtk_events()

    assert quick_connect_widget.connection_state == connection_state.state


def test_quick_connect_widget_requests_vpn_connection_when_connect_button_is_clicked():
    mock_controller = Mock()
    quick_connect_widget = QuickConnectWidget(controller=mock_controller)

    quick_connect_widget.connect_button_click()

    process_gtk_events()

    mock_controller.connect.assert_called_once()


def test_quick_connect_widget_connects_to_fastest_server():
    mock_api = Mock()

    with ThreadPoolExecutor() as thread_pool_executor:
        controller = Controller(thread_pool_executor, mock_api, 0)

        quick_connect_widget = QuickConnectWidget(controller=controller)

        quick_connect_widget.connect_button_click()

        process_gtk_events()

        mock_api.servers.get_fastest_server.assert_called_once()
