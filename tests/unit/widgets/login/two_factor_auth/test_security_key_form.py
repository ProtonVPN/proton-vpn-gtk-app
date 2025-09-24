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

from gi.repository import GLib
import pytest

from proton.vpn.session.exceptions import \
    SecurityKeyError, SecurityKeyNotFoundError, InvalidSecurityKeyError, \
    SecurityKeyTimeoutError, Fido2NotSupportedError, \
    SecurityKeyPINNotSetError, SecurityKeyPINInvalidError
from proton.vpn.session.session import LoginResult

from proton.vpn.app.gtk.controller import Controller
from proton.vpn.app.gtk.widgets.login.two_factor_auth.security_key_form import SecurityKeyForm

from proton.vpn.app.gtk.widgets.main.loading_widget import OverlayWidget
from proton.vpn.app.gtk.widgets.main.notifications import Notifications
from tests.unit.testing_utils import process_gtk_events, run_main_loop


def test_authenticate_button_is_enabled_initialized():
    form = SecurityKeyForm(Mock(), Mock(), Mock())

    assert form.authenticate_button_enabled


def test_authenticate_button_is_disabled_when_pin_code_entry_is_revealed_and_is_empty():
    form = SecurityKeyForm(Mock(), Mock(), Mock())

    form.reveal_pin_code_entry()

    assert not form.authenticate_button_enabled


def test_authenticate_button_is_enabled_when_pin_code_entry_is_revealed_and_is_filled_with_a_pin_code():
    form = SecurityKeyForm(Mock(), Mock(), Mock())

    form.reveal_pin_code_entry()

    form.set_pin_code("123456")
    assert form.authenticate_button_enabled


def test_security_key_form_signals_successful_2fa_when_fido2_assertion_is_successful():
    controller_mock = Mock(spec=Controller)

    assertion_future = Future()
    fido2_assertion = Mock()
    assertion_future.set_result(fido2_assertion)
    controller_mock.generate_2fa_fido2_assertion.return_value = assertion_future

    login_result_future = Future()
    login_result_future.set_result(
        LoginResult(success=True, authenticated=True, twofa_required=False)
    )
    controller_mock.submit_2fa_fido2.return_value = login_result_future

    security_key_form = SecurityKeyForm(
        controller=controller_mock,
        notifications=Mock(),
        overlay_widget=Mock(),
    )
    two_factor_auth_successful_callback = Mock()
    security_key_form.connect(
        "two-factor-auth-successful", two_factor_auth_successful_callback
    )

    security_key_form.authenticate_button_click()

    process_gtk_events()

    cancel_assertion = controller_mock.generate_2fa_fido2_assertion.call_args_list[0][1]["cancel_assertion"]
    controller_mock.generate_2fa_fido2_assertion.assert_called_once_with(
        user_interaction=security_key_form, cancel_assertion=cancel_assertion
    )
    controller_mock.submit_2fa_fido2.assert_called_once_with(fido2_assertion)
    two_factor_auth_successful_callback.assert_called_once()


@pytest.mark.parametrize(
    "exception,error_message",
    [
        (Fido2NotSupportedError(), SecurityKeyForm.FIDO2_NOT_SUPPORTED_MESSAGE),
        (SecurityKeyNotFoundError(), SecurityKeyForm.SECURITY_KEY_NOT_FOUND_MESSAGE),
        (InvalidSecurityKeyError(), SecurityKeyForm.INVALID_SECURITY_KEY_MESSAGE),
        (SecurityKeyTimeoutError(), SecurityKeyForm.GENERIC_ERROR_MESSAGE),
        (SecurityKeyPINNotSetError(), SecurityKeyForm.SECURITY_KEY_PIN_NOT_SET_MESSAGE),
        (SecurityKeyPINInvalidError(), SecurityKeyForm.SECURITY_KEY_PIN_INVALID_MESSAGE),
        (SecurityKeyError(), SecurityKeyForm.GENERIC_ERROR_MESSAGE),
    ]
)
def test_security_key_form_shows_error_message_when_the_fido2_assertion_goes_wrong(
    exception, error_message
):
    controller_mock = Mock(spec=Controller)
    fido2_assertion_future = Future()
    fido2_assertion_future.set_exception(exception)
    controller_mock.generate_2fa_fido2_assertion.return_value = fido2_assertion_future

    notifications_mock = Mock()
    security_key_form = SecurityKeyForm(controller_mock, notifications_mock, Mock())

    security_key_form.authenticate_button_click()

    process_gtk_events()

    notifications_mock.show_error_message.assert_called_once_with(error_message)


def test_security_key_form_shows_overlay_with_message_when_fido2_lib_requests_key_selection(
):
    controller_mock = Mock(spec=Controller)
    overlay_widget =  Mock(spec=OverlayWidget)
    security_key_form = SecurityKeyForm(controller_mock, Mock(spec=Notifications), overlay_widget)

    security_key_form.request_key_selection()

    main_loop = GLib.MainLoop()
    overlay_widget.show_message.side_effect = lambda _: main_loop.quit()
    run_main_loop(main_loop)

    overlay_widget.show_message.assert_called_once_with(SecurityKeyForm.MULTIPLE_SECURITY_KEYS_FOUND)
