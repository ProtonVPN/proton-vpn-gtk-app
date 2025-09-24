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
        controller_mock = Mock(spec=Controller)
        controller_mock.fido2_available = fido2_available
        controller_mock.security_key_env_variable_set = security_key_env_variable_set

        security_key_form = SecurityKeyForm(controller_mock, notifications=Mock(), overlay_widget=Mock())
        two_factor_auth_stack = TwoFactorAuthStack(
            controller=controller_mock,
            notifications=Mock(spec=Notifications),
            overlay_widget=Mock(spec=OverlayWidget),
            security_key_form=security_key_form
        )
        if fido2_available and security_key_env_variable_set:
            assert two_factor_auth_stack.security_key_form
        else:
            assert not two_factor_auth_stack.security_key_form


def test_two_factor_auth_stack_forwards_auth_successful_signal_when_received_from_auth_app_form():
    controller_mock = Mock(spec=Controller)
    controller_mock.fido2_available = False
    controller_mock.security_key_env_variable_set = False

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
    controller_mock.security_key_env_variable_set = True

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

