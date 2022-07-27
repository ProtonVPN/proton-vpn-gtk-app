import time
from concurrent.futures import Future
from unittest.mock import Mock

import pytest

from proton.vpn.app.gtk import Gtk
from proton.vpn.app.gtk.widgets.vpn import VPNWidget


def process_gtk_events(delay=0):
    time.sleep(delay)
    while Gtk.events_pending():
        Gtk.main_iteration_do(blocking=False)


@pytest.fixture
def controller_mocking_successful_logout():
    controller_mock = Mock()

    current_connection_future = Future()
    current_connection_future.set_result(None)

    logout_future = Future()
    logout_future.set_result(None)

    controller_mock.does_current_connection_exists.return_value = current_connection_future
    controller_mock.logout.return_value = logout_future

    return controller_mock


def test_successfull_logout(controller_mocking_successful_logout):
    vpn_widget = VPNWidget(controller_mocking_successful_logout)
    vpn_widget.logout_button_click()

    process_gtk_events()

    controller_mocking_successful_logout.does_current_connection_exists.assert_called_once()
    controller_mocking_successful_logout.logout.assert_called_once()


@pytest.fixture
def controller_mocking_successful_logout_with_current_connection():
    controller_mock = Mock()

    current_connection_future = Future()
    current_connection_future.set_result(True)

    logout_future = Future()
    logout_future.set_result(None)

    disconnect_future = Future()
    disconnect_future.set_result(None)

    controller_mock.does_current_connection_exists.return_value = current_connection_future
    controller_mock.logout.return_value = logout_future
    controller_mock.disconnect.return_value = disconnect_future

    return controller_mock


def test_successfull_logout_with_current_connection(controller_mocking_successful_logout_with_current_connection):
    vpn_widget = VPNWidget(controller_mocking_successful_logout_with_current_connection)
    vpn_widget.logout_button_click()

    process_gtk_events()

    controller_mocking_successful_logout_with_current_connection.logout.assert_not_called()
    assert vpn_widget._logout_dialog is not None
    vpn_widget.close_dialog(True)

    process_gtk_events()

    controller_mocking_successful_logout_with_current_connection.disconnect.assert_called_once()
    controller_mocking_successful_logout_with_current_connection.logout.assert_called_once()
