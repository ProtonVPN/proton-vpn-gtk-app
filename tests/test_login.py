import time
from concurrent.futures import Future
from unittest.mock import Mock

import pytest
from proton.vpn.core_api.session import LoginResult

from proton.vpn.app.gtk import Gtk
from proton.vpn.app.gtk.widgets.login import LoginWidget, LoginForm, TwoFactorAuthForm


def process_gtk_events(delay=0):
    time.sleep(delay)
    while Gtk.events_pending():
        Gtk.main_iteration_do(blocking=False)


def test_login_widget_signals_user_logged_in_when_user_is_authenticated_and_2fa_is_not_required():
    login_widget = LoginWidget(controller=Mock())

    user_logged_in_callback = Mock()
    login_widget.connect("user-logged-in", user_logged_in_callback)

    two_factor_auth_required = False
    login_widget.login_form.emit("user-authenticated", two_factor_auth_required)

    user_logged_in_callback.assert_called_once()


def test_login_widget_asks_for_2fa_when_required():
    login_widget = LoginWidget(controller=Mock())
    two_factor_auth_required = True
    login_widget.login_form.emit("user-authenticated", two_factor_auth_required)

    process_gtk_events()

    assert login_widget.active_form == login_widget.two_factor_auth_form


def test_login_widget_switches_back_to_login_form_if_session_expires_during_2fa():
    login_widget = LoginWidget(controller=Mock())

    login_widget.activate_form(login_widget.two_factor_auth_form)
    login_widget.two_factor_auth_form.emit("session-expired")

    assert login_widget.active_form == login_widget.login_form


@pytest.fixture
def controller_mocking_successful_login():
    controller_mock = Mock()

    login_result_future = Future()
    login_result_future.set_result(
        LoginResult(success=True, authenticated=True, twofa_required=False)
    )
    controller_mock.login.return_value = login_result_future

    return controller_mock


def test_login_form_signals_when_the_user_is_authenticated(
        controller_mocking_successful_login
):
    login_form = LoginForm(controller_mocking_successful_login)
    user_logged_in_callback = Mock()
    login_form.connect("user-authenticated", user_logged_in_callback)

    login_form.username = "username"
    login_form.password = "password"
    login_form.submit_login()

    process_gtk_events()

    controller_mocking_successful_login.login.assert_called_once_with(
        "username", "password"
    )
    two_factor_auth_required = False
    user_logged_in_callback.assert_called_once_with(
        login_form, two_factor_auth_required
    )


@pytest.fixture
def controller_mocking_invalid_username():
    controller_mock = Mock()

    login_result_future = Future()
    login_result_future.set_exception(
        ValueError("Invalid username")
    )
    controller_mock.login.return_value = login_result_future

    return controller_mock


def test_login_form_shows_error_when_submitting_an_invalid_username(
        controller_mocking_invalid_username
):
    login_form = LoginForm(controller_mocking_invalid_username)
    login_form.submit_login()

    process_gtk_events()

    assert login_form.error_message == "Invalid username."


@pytest.fixture
def controller_mocking_invalid_credentials():
    controller_mock = Mock()

    login_result_future = Future()
    login_result_future.set_result(
        LoginResult(success=False, authenticated=False, twofa_required=False)
    )
    controller_mock.login.return_value = login_result_future

    return controller_mock


def test_login_form_shows_error_when_submitting_wrong_credentials(
    controller_mocking_invalid_credentials
):
    login_form = LoginForm(controller_mocking_invalid_credentials)
    login_form.submit_login()

    process_gtk_events()

    assert login_form.error_message == "Wrong credentials."


@pytest.fixture
def controller_mocking_successful_2fa():
    controller_mock = Mock()

    login_result_future = Future()
    login_result_future.set_result(
        LoginResult(success=True, authenticated=True, twofa_required=False)
    )
    controller_mock.submit_2fa_code.return_value = login_result_future

    return controller_mock


def test_two_factor_auth_form_signals_successful_2fa(
        controller_mocking_successful_2fa
):
    two_factor_auth_form = TwoFactorAuthForm(controller_mocking_successful_2fa)
    two_factor_auth_successful_callback = Mock()
    two_factor_auth_form.connect(
        "two-factor-auth-successful", two_factor_auth_successful_callback
    )

    two_factor_auth_form.two_factor_auth_code = "2fa-code"
    two_factor_auth_form.submit_two_factor_auth()

    process_gtk_events()

    controller_mocking_successful_2fa.submit_2fa_code.assert_called_once_with(
        "2fa-code"
    )
    two_factor_auth_successful_callback.assert_called_once()


@pytest.fixture
def controller_mocking_wrong_2fa_code():
    controller_mock = Mock()

    login_result_future = Future()
    login_result_future.set_result(
        LoginResult(success=False, authenticated=True, twofa_required=True)
    )
    controller_mock.submit_2fa_code.return_value = login_result_future

    return controller_mock


def test_two_factor_auth_form_shows_error_when_submitting_wrong_2fa_code(
        controller_mocking_wrong_2fa_code
):
    two_factor_auth_form = TwoFactorAuthForm(controller_mocking_wrong_2fa_code)
    two_factor_auth_form.submit_two_factor_auth()

    process_gtk_events()

    assert two_factor_auth_form.error_message == "Wrong 2FA code."


@pytest.fixture
def controller_mocking_expired_session_before_submitting_2fa_code():
    controller_mock = Mock()

    login_result_future = Future()
    login_result_future.set_result(
        # authenticated is False because the session expired
        LoginResult(success=False, authenticated=False, twofa_required=True)
    )
    controller_mock.submit_2fa_code.return_value = login_result_future

    return controller_mock


def test_two_factor_auth_form_shows_error_when_session_expires_before_submitting_2fa_code(
        controller_mocking_expired_session_before_submitting_2fa_code
):
    two_factor_auth_form = TwoFactorAuthForm(
        controller_mocking_expired_session_before_submitting_2fa_code
    )
    two_factor_auth_form.submit_two_factor_auth()

    process_gtk_events()

    assert two_factor_auth_form.error_message == "Session expired. Please login again."
