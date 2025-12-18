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
from unittest.mock import Mock, patch
from tests.unit.testing_utils import process_gtk_events
from proton.vpn.app.gtk.widgets.headerbar.menu.settings import SettingsWindow
from proton.vpn.app.gtk.widgets.headerbar.menu.settings.common import RECONNECT_MESSAGE


@patch("proton.vpn.app.gtk.widgets.headerbar.menu.settings.settings_window.NotificationBar.show_info_message")
def test_notify_user_with_reconnect_message_display_message_when_user_is_connected_to_openvpn(mock_show_info_message):
    mock_controller = Mock()
    mock_controller.is_connection_active = True
    mock_controller.current_connection.are_feature_updates_applied_when_active = False
    settings_window = SettingsWindow(controller=mock_controller)

    settings_window.notify_user_with_reconnect_message()

    mock_show_info_message.assert_called_once_with(RECONNECT_MESSAGE)


@patch("proton.vpn.app.gtk.widgets.headerbar.menu.settings.settings_window.NotificationBar.show_info_message")
def test_notify_user_with_reconnect_message_do_not_display_message_when_user_is_not_connected(mock_show_info_message):
    mock_controller = Mock()
    mock_controller.is_connection_active = False
    mock_controller.current_connection.are_feature_updates_applied_when_active = False
    settings_window = SettingsWindow(controller=mock_controller)

    settings_window.notify_user_with_reconnect_message()

    mock_show_info_message.assert_not_called()


@patch("proton.vpn.app.gtk.widgets.headerbar.menu.settings.settings_window.NotificationBar.show_info_message")
def test_notify_user_with_reconnect_message_do_not_display_message_when_user_is_connected_to_wireguard(mock_show_info_message):
    mock_controller = Mock()
    mock_controller.is_connection_active = True
    mock_controller.current_connection.are_feature_updates_applied_when_active = True
    settings_window = SettingsWindow(controller=mock_controller)

    settings_window.notify_user_with_reconnect_message()

    mock_show_info_message.assert_not_called()


@pytest.mark.parametrize("is_connection_active,are_feature_updates_applied_when_active,display_message", [
    (True, True, True),
    (False, True, False),
    (True, False, True),
    (False, False, False),
])
@patch("proton.vpn.app.gtk.widgets.headerbar.menu.settings.settings_window.NotificationBar.show_info_message")
def test_notify_user_with_reconnect_message_display_message_when_user_is_connected_and_only_display_message_while_connected_regardless_of_protocol(mock_show_info_message, is_connection_active, are_feature_updates_applied_when_active, display_message):
    mock_controller = Mock()
    mock_controller.is_connection_active = is_connection_active
    mock_controller.current_connection.are_feature_updates_applied_when_active = are_feature_updates_applied_when_active
    settings_window = SettingsWindow(controller=mock_controller)

    settings_window.notify_user_with_reconnect_message(only_notify_on_active_connection=True)

    if display_message:
        mock_show_info_message.assert_called_once()
    else:
        mock_show_info_message.assert_not_called()
