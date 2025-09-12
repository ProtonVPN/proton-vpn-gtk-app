"""
Copyright (c) 2023 Proton AG

This file is part of Proton VPN.

Proton VPN is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Proton VPN is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with ProtonVPN.  If not, see <https://www.gnu.org/licenses/>.
"""
from concurrent.futures import Future
from unittest.mock import Mock

import pytest
from proton.vpn.session.dataclasses import LoginResult

from proton.vpn.app.gtk.widgets.login.two_factor_auth.two_factor_auth_stack import TwoFactorAuthStack
from proton.vpn.app.gtk.widgets.login.two_factor_auth.authenticator_app_form import AuthenticatorAppForm
from proton.vpn.app.gtk.widgets.login.two_factor_auth.security_key_form import SecurityKeyForm
from tests.unit.testing_utils import process_gtk_events
from proton.vpn.session.exceptions import \
    SecurityKeyError, SecurityKeyNotFoundError, InvalidSecurityKeyError, \
    SecurityKeyTimeoutError, Fido2NotSupportedError


SECURITY_KEY_FORM_AUTHENTICATION_VALUE = "SomeTestValue"


@pytest.fixture
def controller_mocking_expired_session_before_submitting_2fa():
    controller_mock = Mock()

    login_result_future = Future()
    login_result_future.set_result(
        # authenticated is False because the session expired
        LoginResult(success=False, authenticated=False, twofa_required=True)
    )
    controller_mock.submit_2fa_code.return_value = login_result_future

    return controller_mock


class TestAuthenticatorAppForm:

    @pytest.fixture
    def controller_mocking_successful_2fa_with_authenticator_app(self):
        controller_mock = Mock()

        login_result_future = Future()
        login_result_future.set_result(
            LoginResult(success=True, authenticated=True, twofa_required=False)
        )
        controller_mock.submit_2fa_code.return_value = login_result_future

        return controller_mock

    def test_two_factor_auth_stack_signals_successful_2fa_with_authenticator_app(
        self, controller_mocking_successful_2fa_with_authenticator_app
    ):
        code = "2fa-code"
        authenticator_app_form = AuthenticatorAppForm()
        two_factor_auth_form = TwoFactorAuthStack(
            controller=controller_mocking_successful_2fa_with_authenticator_app,
            notifications=Mock(),
            overlay_widget=Mock(),
            authenticator_app_form=authenticator_app_form
        )
        two_factor_auth_successful_callback = Mock()
        two_factor_auth_form.connect(
            "two-factor-auth-successful", two_factor_auth_successful_callback
        )

        authenticator_app_form.two_factor_auth_code = code
        authenticator_app_form.authenticate_button_click()

        process_gtk_events()

        controller_mocking_successful_2fa_with_authenticator_app.submit_2fa_code.assert_called_once_with(code)
        two_factor_auth_successful_callback.assert_called_once()

    @pytest.fixture
    def controller_mocking_wrong_2fa_authenticator_app_code(self):
        controller_mock = Mock()

        login_result_future = Future()
        login_result_future.set_result(
            LoginResult(success=False, authenticated=True, twofa_required=True)
        )
        controller_mock.submit_2fa_code.return_value = login_result_future

        return controller_mock

    def test_two_factor_auth_stack_shows_error_when_submitting_wrong_2fa_authenticator_app_code(
        self, controller_mocking_wrong_2fa_authenticator_app_code
    ):
        notifications_mock = Mock()
        authenticator_app_form = AuthenticatorAppForm()

        two_factor_auth_form = TwoFactorAuthStack(
            controller=controller_mocking_wrong_2fa_authenticator_app_code,
            notifications=notifications_mock,
            overlay_widget=Mock(),
            authenticator_app_form=authenticator_app_form
        )
        authenticator_app_form.authenticate_button_click()

        process_gtk_events()

        notifications_mock.show_error_message.assert_called_once_with(two_factor_auth_form.INCORRECT_TWOFA_CODE_MESSAGE)

    def test_two_factor_auth_stack_shows_error_when_session_expires_before_submitting_2fa_authenticator_app_code(
        self, controller_mocking_expired_session_before_submitting_2fa
    ):
        notifications_mock = Mock()
        authenticator_app_form = AuthenticatorAppForm()

        two_factor_auth_form = TwoFactorAuthStack(
            controller=controller_mocking_expired_session_before_submitting_2fa,
            notifications=notifications_mock,
            overlay_widget=Mock(),
            authenticator_app_form=authenticator_app_form
        )
        authenticator_app_form.authenticate_button_click()

        process_gtk_events()

        notifications_mock.show_error_message.assert_called_once_with(two_factor_auth_form.SESSION_EXPIRED_MESSAGE)


    def test_two_factor_auth_stack_display_loading_widget_when_submitting_successful_2fa_authenticator_app_code(
        self, controller_mocking_successful_2fa_with_authenticator_app
    ):
        overlay_widget_mock = Mock()
        authenticator_app_form = AuthenticatorAppForm()

        two_factor_auth_form = TwoFactorAuthStack(
            controller=controller_mocking_successful_2fa_with_authenticator_app,
            notifications=Mock(),
            overlay_widget=overlay_widget_mock,
            authenticator_app_form=authenticator_app_form
        )
        two_factor_auth_successful_callback = Mock()
        two_factor_auth_form.connect(
            "two-factor-auth-successful", two_factor_auth_successful_callback
        )
        authenticator_app_form.two_factor_auth_code = "2fa-code"

        authenticator_app_form.authenticate_button_click()

        widget = overlay_widget_mock.show.call_args[0][0]
        overlay_widget_mock.show.assert_called_once()
        assert widget.get_label() == two_factor_auth_form.LOGGING_IN_MESSAGE

        # When we show the loading widget, it hides the previous one automatically
        overlay_widget_mock.reset_mock()

        process_gtk_events()

        overlay_widget_mock.hide.assert_called_once()

    def test_two_factor_auth_stack_hide_loading_widget_when_when_submitting_wrong_2fa_authenticator_app_code(
        self, controller_mocking_wrong_2fa_authenticator_app_code
    ):
        overlay_widget_mock = Mock()
        authenticator_app_form = AuthenticatorAppForm()
        two_factor_auth_form = TwoFactorAuthStack(
            controller=controller_mocking_wrong_2fa_authenticator_app_code,
            notifications=Mock(),
            overlay_widget=overlay_widget_mock,
            authenticator_app_form=authenticator_app_form
        )
        authenticator_app_form.authenticate_button_click()

        widget = overlay_widget_mock.show.call_args[0][0]
        overlay_widget_mock.show.assert_called_once()
        assert widget.get_label() == two_factor_auth_form.LOGGING_IN_MESSAGE

        # When we show the loading widget, it hides the previous one automatically
        overlay_widget_mock.reset_mock()

        process_gtk_events()

        overlay_widget_mock.hide.assert_called_once()


class TestSecurityKeyForm:

    @pytest.mark.parametrize(
        "fido2_available,security_key_env_variable_set",
        [
            (True, True),
            (True, False),
            (False, True),
            (False, False),
        ]
    )
    def test_two_factor_auth_stack_security_key_form_visibility_when_fido2_and_security_key_env_variable_are_configured(
        self, fido2_available, security_key_env_variable_set
    ):
        controller_mock = Mock()
        controller_mock.fido2_available = fido2_available
        controller_mock.security_key_env_variable_set = security_key_env_variable_set

        security_key_form = SecurityKeyForm()
        two_factor_auth_form = TwoFactorAuthStack(
            controller=controller_mock,
            notifications=Mock(),
            overlay_widget=Mock(),
            security_key_form=security_key_form
        )
        if fido2_available and security_key_env_variable_set:
            assert two_factor_auth_form.security_key_form
        else:
            assert not two_factor_auth_form.security_key_form

    @pytest.fixture
    def controller_mocking_successful_2fa_with_security_key(self):
        controller_mock = Mock()
        controller_mock.fido2_available = True
        controller_mock.security_key_env_variable_set = True

        login_result_future = Future()
        login_result_future.set_result(
            LoginResult(success=True, authenticated=True, twofa_required=False)
        )

        fido2_assertion_future = Future()
        fido2_assertion_future.set_result(SECURITY_KEY_FORM_AUTHENTICATION_VALUE)

        controller_mock.generate_2fa_fido2_assertion.return_value = fido2_assertion_future
        controller_mock.submit_2fa_fido2.return_value = login_result_future

        return controller_mock

    def test_two_factor_auth_stack_signals_successful_2fa_with_security_key(
        self, controller_mocking_successful_2fa_with_security_key
    ):
        code = "2fa-code"
        security_key_form = SecurityKeyForm()
        two_factor_auth_form = TwoFactorAuthStack(
            controller=controller_mocking_successful_2fa_with_security_key,
            notifications=Mock(),
            overlay_widget=Mock(),
            security_key_form=security_key_form
        )
        two_factor_auth_successful_callback = Mock()
        two_factor_auth_form.connect(
            "two-factor-auth-successful", two_factor_auth_successful_callback
        )

        security_key_form.set_pin_code(code)
        security_key_form.authenticate_button_click()

        process_gtk_events()

        controller_mocking_successful_2fa_with_security_key.submit_2fa_fido2.assert_called_once_with(SECURITY_KEY_FORM_AUTHENTICATION_VALUE)
        two_factor_auth_successful_callback.assert_called_once()

    @pytest.mark.parametrize(
        "exception,error_message",
        [
            (Fido2NotSupportedError(), TwoFactorAuthStack.FIDO2_NOT_SUPPORTED_MESSAGE),
            (SecurityKeyNotFoundError(), TwoFactorAuthStack.SECURITY_KEY_NOT_FOUND_MESSAGE),
            (InvalidSecurityKeyError(), TwoFactorAuthStack.INVALID_SECURITY_KEY_MESSAGE),
            (SecurityKeyTimeoutError(), TwoFactorAuthStack.GENERIC_ERROR_MESSAGE),
            (SecurityKeyError(), TwoFactorAuthStack.GENERIC_ERROR_MESSAGE),
        ]
    )
    def test_two_factor_auth_stack_shows_error_when_submitting_2fa_security_key_and_exception_is_raised(
        self, exception, error_message
    ):
        controller_mock = Mock()
        controller_mock.fido2_available = True
        controller_mock.security_key_env_variable_set = True

        login_result_future = Future()
        login_result_future.set_exception(exception)
        controller_mock.generate_2fa_fido2_assertion.return_value = login_result_future

        notifications_mock = Mock()
        security_key_form = SecurityKeyForm()

        two_factor_auth_form = TwoFactorAuthStack(
            controller=controller_mock,
            notifications=notifications_mock,
            overlay_widget=Mock(),
            security_key_form=security_key_form
        )
        security_key_form.authenticate_button_click()

        process_gtk_events()

        notifications_mock.show_error_message.assert_called_once_with(error_message)

    def test_two_factor_auth_stack_shows_error_when_session_expires_before_submitting_2fa_security_key_form(
        self, controller_mocking_expired_session_before_submitting_2fa
    ):
        notifications_mock = Mock()
        security_key_form = SecurityKeyForm()

        two_factor_auth_form = TwoFactorAuthStack(
            controller=controller_mocking_expired_session_before_submitting_2fa,
            notifications=notifications_mock,
            overlay_widget=Mock(),
            authenticator_app_form=security_key_form
        )
        security_key_form.authenticate_button_click()

        process_gtk_events()

        notifications_mock.show_error_message.assert_called_once_with(two_factor_auth_form.SESSION_EXPIRED_MESSAGE)