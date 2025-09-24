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

from proton.vpn.app.gtk.widgets.login.login_widget import LoginStack
from tests.unit.testing_utils import process_gtk_events


def test_login_stack_signals_user_logged_in_when_user_is_authenticated_and_2fa_is_not_required():
    login_stack = LoginStack(controller=Mock(), notifications=Mock(), overlay_widget=Mock())

    user_logged_in_callback = Mock()
    login_stack.connect("user-logged-in", user_logged_in_callback)

    two_factor_auth_required = False
    login_stack.login_form.emit("user-authenticated", two_factor_auth_required)

    user_logged_in_callback.assert_called_once()


def test_login_stack_asks_for_2fa_when_required():
    login_stack = LoginStack(controller=Mock(), notifications=Mock(), overlay_widget=Mock())
    two_factor_auth_required = True
    login_stack.login_form.emit("user-authenticated", two_factor_auth_required)

    process_gtk_events()

    assert login_stack.active_widget == login_stack.two_factor_auth_widget
