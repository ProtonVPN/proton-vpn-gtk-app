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

from proton.vpn.app.gtk.widgets.login.login_widget import KillSwitchSettingEnum, LoginWidget


@pytest.mark.parametrize("killswitch_setting",
                         [KillSwitchSettingEnum.OFF,
                          KillSwitchSettingEnum.ON,
                          KillSwitchSettingEnum.PERMANENT])
def test_login_widget_displays_disable_killswitch_revealer_if_permanent_kill_switch_is_enabled(killswitch_setting):
    controller_mock = Mock()
    controller_mock.get_settings.return_value.killswitch = killswitch_setting
    login_widget = LoginWidget(
        controller=controller_mock,
        notifications=Mock(),
        overlay_widget=Mock(),
        main_window=Mock()
    )

    login_widget.reset()

    assert login_widget.disable_killswitch.get_reveal_child() \
        == (killswitch_setting == KillSwitchSettingEnum.PERMANENT)


def test_login_widget_enables_login_form_and_updates_settings_when_killswitch_is_disabled():
    controller_mock = Mock()
    killswitch_property_mock = PropertyMock()
    type(controller_mock.get_settings.return_value).killswitch = killswitch_property_mock

    login_widget = LoginWidget(
        controller_mock,
        notifications=Mock(),
        overlay_widget=Mock(),
        main_window=Mock()
    )

    login_widget.disable_killswitch.emit("disable-killswitch")

    killswitch_property_mock.assert_called_once_with(KillSwitchSettingEnum.OFF)
    controller_mock.save_settings.assert_called_once()
    assert not login_widget.disable_killswitch.get_reveal_child()
    assert login_widget.login_stack.get_sensitive()
