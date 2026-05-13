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

from proton.vpn.app.gtk.controller import Controller
from proton.vpn.app.gtk.widgets.login.two_factor_auth.two_factor_auth_stack import TwoFactorAuthStack
from proton.vpn.app.gtk.widgets.login.two_factor_auth.security_key_form import SecurityKeyForm
from proton.vpn.app.gtk.widgets.main.loading_widget import OverlayWidget
from proton.vpn.app.gtk.widgets.main.notifications import Notifications
from tests.unit.testing_utils import process_gtk_events



SECURITY_KEY_FORM_AUTHENTICATION_VALUE = "SomeTestValue"


class TestSecurityKeyForm:

    @pytest.mark.parametrize(
        "fido2_available",
        [True, False]
    )
    def test_two_factor_auth_stack_reset_shows_security_key_form_by_default_when_fido2_is_available(
        self, fido2_available
    ):
        controller_mock = Mock(spec=Controller)
        controller_mock.fido2_available = fido2_available

        security_key_form = SecurityKeyForm(controller_mock, notifications=Mock(), overlay_widget=Mock())
        two_factor_auth_stack = TwoFactorAuthStack(
            controller=controller_mock,
            notifications=Mock(spec=Notifications),
            overlay_widget=Mock(spec=OverlayWidget),
            security_key_form=security_key_form
        )

        two_factor_auth_stack.reset()

        if fido2_available:
            assert two_factor_auth_stack.active_widget == two_factor_auth_stack.security_key_form
        else:
            assert two_factor_auth_stack.active_widget == two_factor_auth_stack.authenticator_app_form


def test_two_factor_auth_stack_forwards_auth_successful_signal_when_received_from_auth_app_form():
    controller_mock = Mock(spec=Controller)
    controller_mock.fido2_available = False

    two_factor_auth_stack = TwoFactorAuthStack(
        controller=controller_mock,
        notifications=Mock(spec=Notifications),
        overlay_widget=Mock(spec=OverlayWidget),
    )

    two_factor_auth_successful_callback = Mock()
    two_factor_auth_stack.connect("two-factor-auth-successful", two_factor_auth_successful_callback)

    two_factor_auth_stack.authenticator_app_form.emit("two-factor-auth-successful")

    process_gtk_events()

    two_factor_auth_successful_callback.assert_called_once_with(two_factor_auth_stack)


def test_two_factor_auth_stack_forwards_auth_successful_signal_when_received_from_security_key_app_form():
    controller_mock = Mock(spec=Controller)
    controller_mock.fido2_available = True

    two_factor_auth_stack = TwoFactorAuthStack(
        controller=controller_mock,
        notifications=Mock(spec=Notifications),
        overlay_widget=Mock(spec=OverlayWidget),
    )

    two_factor_auth_successful_callback = Mock()
    two_factor_auth_stack.connect("two-factor-auth-successful", two_factor_auth_successful_callback)

    two_factor_auth_stack.security_key_form.emit("two-factor-auth-successful")

    process_gtk_events()

    two_factor_auth_successful_callback.assert_called_once_with(two_factor_auth_stack)


def test_two_factor_auth_stack_logs_user_out_when_security_key_2fa_is_cancelled():
    controller = Mock(spec=Controller)
    logout_future = Mock()
    logout_future.add_done_callback.side_effect = lambda cb: cb(logout_future)
    controller.logout.return_value = logout_future

    two_factor_auth_stack = TwoFactorAuthStack(
        controller=controller,
        notifications=Mock(spec=Notifications),
        overlay_widget=Mock(spec=OverlayWidget)
    )
    two_factor_auth_stack.security_key_form.emit("two-factor-auth-cancelled")

    process_gtk_events()

    controller.logout.assert_called_once()


def test_two_factor_auth_stack_logs_user_out_when_authenticator_app_2fa_is_cancelled():
    controller = Mock(spec=Controller)
    logout_future = Mock()
    logout_future.add_done_callback.side_effect = lambda cb: cb(logout_future)
    controller.logout.return_value = logout_future

    two_factor_auth_stack = TwoFactorAuthStack(
        controller=controller,
        notifications=Mock(spec=Notifications),
        overlay_widget=Mock(spec=OverlayWidget)
    )
    two_factor_auth_stack.authenticator_app_form.emit("two-factor-auth-cancelled")

    process_gtk_events()

    controller.logout.assert_called_once()
