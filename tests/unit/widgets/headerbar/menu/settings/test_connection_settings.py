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
from unittest.mock import Mock, PropertyMock, patch, MagicMock
from proton.vpn.app.gtk.widgets.headerbar.menu.settings.connection_settings import ConnectionSettings, ToggleWidget, ComboboxWidget


FREE_TIER = 0
PLUS_TIER = 1


@patch("proton.vpn.app.gtk.widgets.headerbar.menu.settings.connection_settings.ConnectionSettings.pack_start")
@patch("proton.vpn.app.gtk.widgets.headerbar.menu.settings.connection_settings.ToggleWidget")
def test_build_vpn_accelerator_save_new_value_when_callback_is_called(toggle_widget_mock, _):
    controller_mock = Mock()
    controller_mock.user_tier = FREE_TIER
    settings_window_mock = Mock()
    cs = ConnectionSettings(controller_mock, settings_window_mock)
    cs.build_vpn_accelerator()
    new_value = False

    toggle_widget = toggle_widget_mock.call_args[1]
    callback = toggle_widget["callback"]

    callback(None, new_value, toggle_widget_mock)

    toggle_widget_mock.save_setting.assert_called_once_with(new_value)
    settings_window_mock.notify_user_with_reconnect_message.assert_called_once()


@patch("proton.vpn.app.gtk.widgets.headerbar.menu.settings.connection_settings.ConnectionSettings.pack_start")
@patch("proton.vpn.app.gtk.widgets.headerbar.menu.settings.connection_settings.ToggleWidget")
def test_build_moderate_nat_save_new_value_when_callback_is_called(toggle_widget_mock, _):
    controller_mock = Mock()
    controller_mock.user_tier = FREE_TIER
    settings_window_mock = Mock()
    cs = ConnectionSettings(controller_mock, settings_window_mock)
    cs.build_moderate_nat()
    new_value = False

    toggle_widget = toggle_widget_mock.call_args[1]
    callback = toggle_widget["callback"]

    callback(None, new_value, toggle_widget_mock)

    toggle_widget_mock.save_setting.assert_called_once_with(new_value)
    settings_window_mock.notify_user_with_reconnect_message.assert_called_once()


@patch("proton.vpn.app.gtk.widgets.headerbar.menu.settings.connection_settings.ConnectionSettings.pack_start")
@patch("proton.vpn.app.gtk.widgets.headerbar.menu.settings.connection_settings.ToggleWidget")
def test_build_ipv6_save_new_value_when_callback_is_called(toggle_widget_mock, _):
    controller_mock = Mock()
    settings_window_mock = Mock()
    cs = ConnectionSettings(controller_mock, settings_window_mock)
    cs.build_ipv6()
    new_value = False

    toggle_widget = toggle_widget_mock.call_args[1]
    callback = toggle_widget["callback"]

    callback(None, new_value, toggle_widget_mock)

    toggle_widget_mock.save_setting.assert_called_once_with(new_value)
    settings_window_mock.notify_user_with_reconnect_message.assert_called_once()
