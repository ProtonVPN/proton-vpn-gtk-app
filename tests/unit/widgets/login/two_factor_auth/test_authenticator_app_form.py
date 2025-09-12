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

from proton.vpn.app.gtk.widgets.login.two_factor_auth.authenticator_app_form import AuthenticatorAppForm


def test_authenticator_app_form_toggle_authentication_mode_when_clicking_on_toggle_authentication_mode_button():
    two_factor_auth_form = AuthenticatorAppForm()

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
    two_factor_auth_form = AuthenticatorAppForm()

    assert not two_factor_auth_form.authenticate_button_enabled
    assert not two_factor_auth_form.code

    two_factor_auth_form.code = "123456"
    assert two_factor_auth_form.authenticate_button_enabled


def test_authenticate_button_disables_when_amount_of_required_characters_are_provided_for_twofa_and_toggle_authentication_mode_is_clicked():
    two_factor_auth_form = AuthenticatorAppForm()

    two_factor_auth_form.code = "123456"
    assert two_factor_auth_form.authenticate_button_enabled

    two_factor_auth_form.toggle_authentication_button_click()

    assert not two_factor_auth_form.authenticate_button_enabled


def test_authenticate_button_enables_when_amount_of_required_characters_are_provided_for_recovery_authentication_mode():
    two_factor_auth_form = AuthenticatorAppForm()

    two_factor_auth_form.toggle_authentication_button_click()

    two_factor_auth_form.code = "12345678"
    assert two_factor_auth_form.authenticate_button_enabled


def test_authenticate_button_disables_when_amount_of_required_characters_are_provided_for_recovery_and_toggle_authentication_mode_is_clicked():
    two_factor_auth_form = AuthenticatorAppForm()

    two_factor_auth_form.toggle_authentication_button_click()

    two_factor_auth_form.code = "12345678"
    assert two_factor_auth_form.authenticate_button_enabled

    two_factor_auth_form.toggle_authentication_button_click()

    assert not two_factor_auth_form.authenticate_button_enabled