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
from unittest.mock import Mock

from proton.vpn.app.gtk.widgets.login.two_factor_auth.security_key_form import SecurityKeyForm, SecurityKeyFormData


def test_authenticate_button_is_enabled_initialized():
    form = SecurityKeyForm()

    assert form.authenticate_button_enabled


def test_authenticate_button_is_disabled_when_pin_code_entry_is_revealed_and_is_empty():
    form = SecurityKeyForm()

    form.reveal_pin_code_entry()

    assert not form.authenticate_button_enabled


def test_authenticate_button_is_enabled_when_pin_code_entry_is_revealed_and_is_filled_with_a_pin_code():
    form = SecurityKeyForm()

    form.reveal_pin_code_entry()

    form.set_pin_code("123456")
    assert form.authenticate_button_enabled


def test_authenticate_button_clicked_signal_is_emitted_when_authenticate_button_is_clicked():
    form = SecurityKeyForm()

    mock_callback = Mock()
    form.connect("authenticate-button-clicked", mock_callback)

    form.authenticate_button_click()
    mock_callback.assert_called_once_with(form, SecurityKeyFormData())
