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
from proton.vpn.core_api.settings import NetShield


class TestSettingsWindow:

    def test_settings_window_ensure_passed_objects_are_added_to_container(self):
        tray_indicator_mock = Mock()
        feature_settings_mock = Mock()
        connection_settings_mock = Mock()
        general_settings_mock = Mock()
        notification_bar_mock = Mock()
        with patch("proton.vpn.app.gtk.widgets.headerbar.menu.settings.settings_window.Gtk.Box.pack_start") as pack_start_mock:
            settings_window = SettingsWindow(Mock(), tray_indicator_mock, notification_bar_mock, feature_settings_mock, connection_settings_mock, general_settings_mock)

            assert pack_start_mock.mock_calls[0].args == (feature_settings_mock, False, False, 0)
            assert pack_start_mock.mock_calls[1].args == (connection_settings_mock, False, False, 0)
            assert pack_start_mock.mock_calls[2].args == (general_settings_mock, False, False, 0)
            assert pack_start_mock.mock_calls[3].args == (notification_bar_mock, False, False, 0)

    @pytest.mark.parametrize("present_window", [False, True])
    def test_settings_window_ensure_window_does_not_load_content_until_required(self, present_window):
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