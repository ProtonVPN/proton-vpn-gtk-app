import time
from concurrent.futures import Future
from unittest.mock import Mock

import pytest
from proton.vpn.core_api.session import LoginResult

from proton.vpn.app.gtk import Gtk
from proton.vpn.app.gtk.widgets.login import LoginWidget


def process_gtk_events(delay=0):
    time.sleep(delay)
    while Gtk.events_pending():
        Gtk.main_iteration_do(blocking=False)


@pytest.fixture
def controller_mocking_successful_login():
    controller_mock = Mock()

    login_result_future = Future()
    login_result_future.set_result(
        LoginResult(success=True, authenticated=True, twofa_required=False)
    )
    controller_mock.login.return_value = login_result_future

    return controller_mock


def test_login_widget_signals_when_the_user_is_logged_in(
        controller_mocking_successful_login
):
    login_widget = LoginWidget(controller_mocking_successful_login)
    user_logged_in_callback = Mock()
    login_widget.connect("user-logged-in", user_logged_in_callback)

    login_widget.username = "username"
    login_widget.password = "password"
    login_widget.submit_login()

    process_gtk_events()

    controller_mocking_successful_login.login.assert_called_once_with(
        "username", "password"
    )
    user_logged_in_callback.assert_called_once()


@pytest.fixture
def controller_mocking_2fa_required():
    controller_mock = Mock()

    login_result_future = Future()
    login_result_future.set_result(
        LoginResult(success=False, authenticated=True, twofa_required=True)
    )
    controller_mock.login.return_value = login_result_future

    return controller_mock


def test_login_widget_asks_for_2fa_when_required(
        controller_mocking_2fa_required
):
    login_widget = LoginWidget(controller_mocking_2fa_required)

    login_widget.username = "username"
    login_widget.password = "password"
    login_widget.submit_login()

    process_gtk_events()

    assert login_widget.is_two_factor_auth_active()


@pytest.fixture
def controller_mocking_successful_2fa():
    controller_mock = Mock()

    login_result_future = Future()
    login_result_future.set_result(
        LoginResult(success=True, authenticated=True, twofa_required=False)
    )
    controller_mock.submit_2fa_code.return_value = login_result_future

    return controller_mock


def test_login_widget_signals_user_is_logged_in_after_successful_2fa(
        controller_mocking_successful_2fa
):
    login_widget = LoginWidget(controller_mocking_successful_2fa)
    user_logged_in_callback = Mock()
    login_widget.connect("user-logged-in", user_logged_in_callback)

    login_widget.two_factor_auth_code = "2fa-code"
    login_widget.submit_two_factor_auth()

    process_gtk_events()

    controller_mocking_successful_2fa.submit_2fa_code.assert_called_once_with(
        "2fa-code"
    )
    user_logged_in_callback.assert_called_once()
