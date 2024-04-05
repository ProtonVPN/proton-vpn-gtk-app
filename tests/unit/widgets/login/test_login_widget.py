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
import pytest
from unittest.mock import Mock, patch, PropertyMock

from proton.vpn.app.gtk.widgets.login.login_widget import LoginStack, KillSwitchSettingEnum, LoginWidget
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

    assert login_stack.active_form == login_stack.two_factor_auth_form


def test_login_stack_switches_back_to_login_form_if_session_expires_during_2fa():
    login_stack = LoginStack(controller=Mock(), notifications=Mock(), overlay_widget=Mock())

    login_stack.display_form(login_stack.two_factor_auth_form)
    login_stack.two_factor_auth_form.emit("session-expired")

    assert login_stack.active_form == login_stack.login_form


@patch("proton.vpn.app.gtk.widgets.login.login_widget.Gtk.Box.pack_start")
@patch("proton.vpn.app.gtk.widgets.login.login_widget.Gtk.Box.pack_end")
@pytest.mark.parametrize("killswitch_setting", [KillSwitchSettingEnum.OFF, KillSwitchSettingEnum.ON, KillSwitchSettingEnum.PERMANENT])
def test_login_widget_displays_disable_killswitch_revealer_if_permanent_kill_switch_is_enabled(pack_end_mock, pack_start_mock, killswitch_setting):
    controller_mock = Mock()
    disable_killswitch_widget_mock = Mock()
    login_stack_mock = Mock()
    controller_mock.get_settings.return_value.killswitch = killswitch_setting
    login_widget = LoginWidget(
        controller=controller_mock, notifications=Mock(), overlay_widget=Mock(),
        main_window=Mock(), login_stack=login_stack_mock, disable_killswitch_widget=disable_killswitch_widget_mock
    )

    login_widget.reset()

    disable_killswitch_widget_mock.set_reveal_child.assert_called_once_with(
        killswitch_setting == KillSwitchSettingEnum.PERMANENT
    )


@patch("proton.vpn.app.gtk.widgets.login.login_widget.Gtk.Box.pack_start")
@patch("proton.vpn.app.gtk.widgets.login.login_widget.Gtk.Box.pack_end")
def test_login_widget_enables_login_form_and_updates_settings_when_killswitch_is_disabled(pack_end_mock, pack_start_mock):
    controller_mock = Mock()
    killswitch_property_mock = PropertyMock()
    type(controller_mock.get_settings.return_value).killswitch = killswitch_property_mock
    disable_killswitch_widget_mock = Mock()
    login_stack_mock = Mock()

    LoginWidget(
        controller_mock, notifications=Mock(), overlay_widget=Mock(),
        main_window=Mock(), login_stack=login_stack_mock, disable_killswitch_widget=disable_killswitch_widget_mock
    )

    callback = disable_killswitch_widget_mock.connect.mock_calls[0].args[1]
    callback(None)

    killswitch_property_mock.assert_called_once_with(KillSwitchSettingEnum.OFF)
    controller_mock.save_settings.assert_called_once()
    disable_killswitch_widget_mock.set_reveal_child.assert_called_once_with(False)
    login_stack_mock.login_form.set_property.assert_called_once_with("sensitive", True)
