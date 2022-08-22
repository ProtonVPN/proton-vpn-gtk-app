from concurrent.futures import Future
from unittest.mock import Mock

import pytest

from proton.vpn.app.gtk.widgets.vpn import VPNWidget
from proton.vpn.core_api.exceptions import VPNConnectionFoundAtLogout

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

    disconnect_future = Future()
    disconnect_future.set_result(None)

    controller_mock.logout.side_effect = [logout_future_raises_exception, logout_future_success]
    controller_mock.disconnect.return_value = disconnect_future

    return controller_mock


def test_successful_logout_with_current_connection(controller_mocking_successful_logout_with_current_connection):
    vpn_widget = VPNWidget(controller_mocking_successful_logout_with_current_connection)
    vpn_widget.logout_button_click()

    process_gtk_events()

    controller_mocking_successful_logout_with_current_connection.logout.assert_called_once()
    assert vpn_widget._logout_dialog is not None
    vpn_widget.close_dialog(True)

    process_gtk_events()

    controller_mocking_successful_logout_with_current_connection.disconnect.assert_called_once()
    assert controller_mocking_successful_logout_with_current_connection.logout.call_count == 2
