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
from unittest.mock import Mock, PropertyMock, patch
from tests.unit.testing_utils import process_gtk_events
from proton.vpn.app.gtk.widgets.headerbar.menu.settings import SettingsWindow
from proton.vpn.core.settings import NetShield
from proton.vpn.app.gtk.widgets.main.notification_bar import NotificationBar
from proton.vpn.app.gtk.widgets.headerbar.menu.settings.common import RECONNECT_MESSAGE


def test_settings_window_ensure_passed_objects_are_added_to_container():
    tray_indicator_mock = Mock(name="tray_indicator")
    feature_settings_mock = Mock(name="feature_settings")
    connection_settings_mock = Mock(name="connection_settings")
    general_settings_mock = Mock(name="general_settings")
    notification_bar_mock = Mock(name="notification_bar")
    account_settings_mock = Mock(name="account_settings")
    with patch("proton.vpn.app.gtk.widgets.headerbar.menu.settings.settings_window.Gtk.Box.pack_start") as pack_start_mock:
        settings_window = SettingsWindow(
            Mock(),
            tray_indicator_mock, notification_bar_mock, feature_settings_mock,
            connection_settings_mock, general_settings_mock, account_settings_mock
        )

        print(pack_start_mock.mock_calls)

        assert pack_start_mock.mock_calls[0].args == (account_settings_mock, False, False, 0)
        assert pack_start_mock.mock_calls[1].args == (feature_settings_mock, False, False, 0)
        assert pack_start_mock.mock_calls[2].args == (connection_settings_mock, False, False, 0)
        assert pack_start_mock.mock_calls[3].args == (general_settings_mock, False, False, 0)
        assert pack_start_mock.mock_calls[4].args == (notification_bar_mock, False, False, 0)

@pytest.mark.parametrize("present_window", [False, True])
def test_settings_window_ensure_window_does_not_load_content_until_required(present_window):
    connection_settings = Mock()
    with patch("proton.vpn.app.gtk.widgets.headerbar.menu.settings.settings_window.Gtk.Box.pack_start") as pack_start_mock:
        settings_window = SettingsWindow(Mock(), Mock(), connection_settings)

        if present_window:
            # FIX-ME: Calling `settings_window.present()` for some reason causes
            # tests/unit/widgets/main/test_main_window.py tests to fail
            # settings_window.present()
            # process_gtk_events()
            # connection_settings.build_ui.assert_called_once()
            pass
        else:
            connection_settings.build_ui.assert_not_called()


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
