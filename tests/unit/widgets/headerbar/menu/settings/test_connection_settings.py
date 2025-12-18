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

from unittest.mock import Mock, patch
from proton.vpn.app.gtk.widgets.headerbar.menu.settings.connection_settings import ConnectionSettings
from proton.vpn.app.gtk.controller import Controller

FREE_TIER = 0
PLUS_TIER = 1


def test_build_vpn_accelerator_save_new_value_when_callback_is_called():
    controller_mock = Mock(spec=Controller)
    controller_mock.user_tier = PLUS_TIER
    settings_window_mock = Mock()
    cs = ConnectionSettings(controller_mock, settings_window_mock)
    cs.build_vpn_accelerator()
    new_value = False

    toggle_widget = cs.get_last_child()
    toggle_widget.switch.set_active(new_value)

    controller_mock.save_setting_attr.assert_called_once_with("settings.features.vpn_accelerator", new_value)
    settings_window_mock.notify_user_with_reconnect_message.assert_not_called()


def test_build_moderate_nat_save_new_value_when_callback_is_called():
    controller_mock = Mock()
    controller_mock.user_tier = PLUS_TIER
    settings_window_mock = Mock()
    cs = ConnectionSettings(controller_mock, settings_window_mock)
    cs.build_moderate_nat()
    new_value = False

    toggle_widget = cs.get_last_child()
    toggle_widget.switch.set_active(new_value)

    controller_mock.save_setting_attr.assert_called_once_with("settings.features.moderate_nat", new_value)
    settings_window_mock.notify_user_with_reconnect_message.assert_not_called()


def test_build_ipv6_save_new_value_when_callback_is_called():
    controller_mock = Mock()
    controller_mock.user_tier = PLUS_TIER
    settings_window_mock = Mock()
    cs = ConnectionSettings(controller_mock, settings_window_mock)
    cs.build_ipv6()
    new_value = False

    toggle_widget = cs.get_last_child()
    toggle_widget.switch.set_active(new_value)

    controller_mock.save_setting_attr.assert_called_once_with("settings.ipv6", new_value)
    settings_window_mock.notify_user_with_reconnect_message.assert_called_once()
