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

from proton.vpn.app.gtk.widgets.login.login_widget import LoginWidget
from tests.unit.utils import process_gtk_events


def test_login_widget_signals_user_logged_in_when_user_is_authenticated_and_2fa_is_not_required():
    login_widget = LoginWidget(controller=Mock(), notifications=Mock())

    user_logged_in_callback = Mock()
    login_widget.connect("user-logged-in", user_logged_in_callback)

    two_factor_auth_required = False
    login_widget.login_form.emit("user-authenticated", two_factor_auth_required)

    user_logged_in_callback.assert_called_once()


def test_login_widget_asks_for_2fa_when_required():
    login_widget = LoginWidget(controller=Mock(), notifications=Mock())
    two_factor_auth_required = True
    login_widget.login_form.emit("user-authenticated", two_factor_auth_required)

    process_gtk_events()

    assert login_widget.active_form == login_widget.two_factor_auth_form


def test_login_widget_switches_back_to_login_form_if_session_expires_during_2fa():
    login_widget = LoginWidget(controller=Mock(), notifications=Mock())

    login_widget.display_form(login_widget.two_factor_auth_form)
    login_widget.two_factor_auth_form.emit("session-expired")

    assert login_widget.active_form == login_widget.login_form
