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

from proton.vpn.app.gtk.controller import Controller
from proton.vpn.app.gtk.widgets.login.two_factor_auth.authenticator_app_form import AuthenticatorAppForm

from proton.vpn.app.gtk.widgets.main.loading_widget import OverlayWidget
from proton.vpn.app.gtk.widgets.main.notifications import Notifications
from tests.unit.testing_utils import process_gtk_events


@pytest.fixture
def controller_mocking_successful_2fa_with_authenticator_app():
    controller_mock = Mock()

    login_result_future = Future()
    login_result_future.set_result(
        LoginResult(success=True, authenticated=True, twofa_required=False)
    )
    controller_mock.submit_2fa_code.return_value = login_result_future

    return controller_mock

def test_authenticator_app_form_signals_successful_2fa_when_code_is_correct(
    controller_mocking_successful_2fa_with_authenticator_app
):
    code = "2fa-code"
    authenticator_app_form = AuthenticatorAppForm(
        controller=controller_mocking_successful_2fa_with_authenticator_app,
        notifications=Mock(),
        overlay_widget=Mock(),
    )
    two_factor_auth_successful_callback = Mock()
    authenticator_app_form.connect(
        "two-factor-auth-successful", two_factor_auth_successful_callback
    )

    authenticator_app_form.two_factor_auth_code = code
    authenticator_app_form.authenticate_button_click()

    process_gtk_events()

    controller_mocking_successful_2fa_with_authenticator_app.submit_2fa_code.assert_called_once_with(code)
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

def test_authenticator_app_form_shows_error_message_when_code_is_incorrect(
    controller_mocking_wrong_2fa_code
):
    code = "2fa-code"
    notifications = Mock(spec=Notifications)
    authenticator_app_form = AuthenticatorAppForm(
        controller=controller_mocking_wrong_2fa_code,
        notifications=notifications,
        overlay_widget=Mock(spec=OverlayWidget),
    )

    authenticator_app_form.two_factor_auth_code = code
    authenticator_app_form.authenticate_button_click()

    process_gtk_events()

    controller_mocking_wrong_2fa_code.submit_2fa_code.assert_called_once_with(code)
    notifications.show_error_message.assert_called_once_with(AuthenticatorAppForm.INCORRECT_TWOFA_CODE_MESSAGE)

def test_authenticator_app_form_displays_loading_widget_after_submitting_2fa__code():
    controller_mock = Mock(spec=Controller)
    controller_mock.submit_2fa_code.return_value = Future()
    overlay_widget_mock = Mock(spec=OverlayWidget)

    authenticator_app_form = AuthenticatorAppForm(
        controller=controller_mock,
        notifications=Mock(spec=Notifications),
        overlay_widget=overlay_widget_mock,
    )
    authenticator_app_form.two_factor_auth_code = "2fa-code"

    authenticator_app_form.authenticate_button_click()

    process_gtk_events()

    overlay_widget_mock.show_message.assert_called_once_with(AuthenticatorAppForm.LOGGING_IN_MESSAGE)


def test_authenticator_app_hides_loading_widget_after_2fa_api_response(
    controller_mocking_wrong_2fa_code
):
    overlay_widget_mock = Mock(spec=OverlayWidget)
    authenticator_app_form = AuthenticatorAppForm(
        controller=controller_mocking_wrong_2fa_code,
        notifications=Mock(Notifications),
        overlay_widget=overlay_widget_mock
    )
    authenticator_app_form.authenticate_button_click()

    overlay_widget_mock.show_message.assert_called_once_with(AuthenticatorAppForm.LOGGING_IN_MESSAGE)

    # When we show the loading widget, it hides the previous one automatically
    overlay_widget_mock.reset_mock()

    process_gtk_events()

    overlay_widget_mock.hide.assert_called_once()


def test_authenticator_app_form_toggle_authentication_mode_when_clicking_on_toggle_authentication_mode_button():
    two_factor_auth_form = AuthenticatorAppForm(
        controller=Mock(spec=Controller),
        notifications=Mock(spec=Notifications),
        overlay_widget=Mock(spec=OverlayWidget)
    )

    assert two_factor_auth_form.help_label == two_factor_auth_form.TWOFA_HELP_LABEL
    assert two_factor_auth_form.code_entry_placeholder == two_factor_auth_form.TWOFA_ENTRY_PLACEHOLDER
    assert two_factor_auth_form.limit_clarification == two_factor_auth_form.TWOFA_ENTRY_LIMIT_CLARIFICATION
    assert two_factor_auth_form.toggle_authentication_mode_button_label == two_factor_auth_form.TWOFA_TOGGLE_AUTHENICATION_MODE_LABEL

    two_factor_auth_form.toggle_authentication_button_click()

    assert two_factor_auth_form.help_label == two_factor_auth_form.RECOVERY_HELP_LABEL
    assert two_factor_auth_form.code_entry_placeholder == two_factor_auth_form.RECOVERY_ENTRY_PLACEHOLDER
    assert two_factor_auth_form.limit_clarification == two_factor_auth_form.RECOVERY_ENTRY_LIMIT_CLARIFICATION
    assert two_factor_auth_form.toggle_authentication_mode_button_label == two_factor_auth_form.RECOVERY_TOGGLE_AUTHENICATION_MODE_LABEL

    two_factor_auth_form.toggle_authentication_button_click()

    assert two_factor_auth_form.help_label == two_factor_auth_form.TWOFA_HELP_LABEL
    assert two_factor_auth_form.code_entry_placeholder == two_factor_auth_form.TWOFA_ENTRY_PLACEHOLDER
    assert two_factor_auth_form.limit_clarification == two_factor_auth_form.TWOFA_ENTRY_LIMIT_CLARIFICATION
    assert two_factor_auth_form.toggle_authentication_mode_button_label == two_factor_auth_form.TWOFA_TOGGLE_AUTHENICATION_MODE_LABEL


def test_authenticate_button_enables_when_amount_of_required_characters_are_provided_for_twofa_authentication_mode():
    two_factor_auth_form = AuthenticatorAppForm(
        controller=Mock(spec=Controller),
        notifications=Mock(spec=Notifications),
        overlay_widget=Mock(spec=OverlayWidget)
    )

    assert not two_factor_auth_form.authenticate_button_enabled
    assert not two_factor_auth_form.code

    two_factor_auth_form.code = "123456"
    assert two_factor_auth_form.authenticate_button_enabled


def test_authenticate_button_disables_when_amount_of_required_characters_are_provided_for_twofa_and_toggle_authentication_mode_is_clicked():
    two_factor_auth_form = AuthenticatorAppForm(
        controller=Mock(spec=Controller),
        notifications=Mock(spec=Notifications),
        overlay_widget=Mock(spec=OverlayWidget)
    )

    two_factor_auth_form.code = "123456"
    assert two_factor_auth_form.authenticate_button_enabled

    two_factor_auth_form.toggle_authentication_button_click()

    assert not two_factor_auth_form.authenticate_button_enabled


def test_authenticate_button_enables_when_amount_of_required_characters_are_provided_for_recovery_authentication_mode():
    two_factor_auth_form = AuthenticatorAppForm(
        controller=Mock(spec=Controller),
        notifications=Mock(spec=Notifications),
        overlay_widget=Mock(spec=OverlayWidget)
    )

    two_factor_auth_form.toggle_authentication_button_click()

    two_factor_auth_form.code = "12345678"
    assert two_factor_auth_form.authenticate_button_enabled


def test_authenticate_button_disables_when_amount_of_required_characters_are_provided_for_recovery_and_toggle_authentication_mode_is_clicked():
    two_factor_auth_form = AuthenticatorAppForm(
        controller=Mock(spec=Controller),
        notifications=Mock(spec=Notifications),
        overlay_widget=Mock(spec=OverlayWidget)
    )

    two_factor_auth_form.toggle_authentication_button_click()

    two_factor_auth_form.code = "12345678"
    assert two_factor_auth_form.authenticate_button_enabled

    two_factor_auth_form.toggle_authentication_button_click()

    assert not two_factor_auth_form.authenticate_button_enabled