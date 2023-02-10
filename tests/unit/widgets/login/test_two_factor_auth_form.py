from concurrent.futures import Future
from unittest.mock import Mock

import pytest
from proton.vpn.session.dataclasses import LoginResult

from proton.vpn.app.gtk.widgets.login.two_factor_auth_form import TwoFactorAuthForm
from tests.unit.utils import process_gtk_events


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
