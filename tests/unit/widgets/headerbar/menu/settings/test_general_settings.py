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
from proton.vpn.app.gtk import gi
from gi.repository import Gdk  # pylint: disable=C0413 # noqa: E402
from proton.vpn.app.gtk.widgets.headerbar.menu.settings.general_settings import GeneralSettings, TrayPinnedServersWidget, EntryWidget


class TestGeneralSettings:

    @patch("proton.vpn.app.gtk.widgets.headerbar.menu.settings.general_settings.GeneralSettings.pack_start")
    @patch("proton.vpn.app.gtk.widgets.headerbar.menu.settings.general_settings.EntryWidget")
    def test_build_connect_at_app_startup_saves_value_when_callback_is_called(self, entry_widget_mock, _):
        value_to_store = "new value"
        gs = GeneralSettings(Mock())
        gs.build_connect_at_app_startup()

        gtk_entry_mock = Mock()
        gtk_entry_mock.get_text.return_value = "new value"

        callback = entry_widget_mock.call_args[1]["callback"]
        callback(gtk_entry_mock, None, entry_widget_mock)

        entry_widget_mock.save_setting.assert_called_once_with(value_to_store.upper())

    @patch("proton.vpn.app.gtk.widgets.headerbar.menu.settings.general_settings.GeneralSettings.pack_start")
    @patch("proton.vpn.app.gtk.widgets.headerbar.menu.settings.general_settings.EntryWidget")
    def test_build_connect_at_app_startup_populates_disabled_with_off(self, entry_widget_mock, _):
        gs = GeneralSettings(Mock())
        gs.build_connect_at_app_startup()

        gtk_entry_mock = Mock()
        gtk_entry_mock.get_text.return_value = "off"

        callback = entry_widget_mock.call_args[1]["callback"]
        callback(gtk_entry_mock, None, entry_widget_mock)

        entry_widget_mock.save_setting.assert_called_once_with(None)

    @patch("proton.vpn.app.gtk.widgets.headerbar.menu.settings.general_settings.GeneralSettings.pack_start")
    @patch("proton.vpn.app.gtk.widgets.headerbar.menu.settings.general_settings.EarlyAccessWidget")
    def test_build_beta_upgrade_is_only_displayed_if_condition_allows_it(self, early_access_widget, pack_start):
        early_access_widget_return_mock = Mock()
        early_access_widget_return_mock.can_early_access_be_displayed.return_value = False
        early_access_widget.return_value = early_access_widget_return_mock

        gs = GeneralSettings(Mock())
        gs.build_beta_upgrade()

        # The call count here is 1 because:
        # 1st time it's called inside class BaseCategoryContainer to add the category header, which is inherited by EarlyAccessWidget
        # 2nd time it's called only if the can_early_access_be_displayed is true, otherwise it does not add the widget to be displayed
        assert pack_start.call_count == 1

    @pytest.mark.parametrize("tray_indicator_mock", [None, Mock()])
    @patch("proton.vpn.app.gtk.widgets.headerbar.menu.settings.general_settings.GeneralSettings.build_start_app_minimized")
    @patch("proton.vpn.app.gtk.widgets.headerbar.menu.settings.general_settings.GeneralSettings.build_tray_pinned_servers")
    def test_display_start_app_minimized_and_tray_pinned_servers_if_tray_indicator_is_found(self, build_tray_pinned_servers_mock, build_start_app_minimized_mock, tray_indicator_mock):
        gs = GeneralSettings(Mock(), tray_indicator=tray_indicator_mock)
        gs.build_ui()

        if tray_indicator_mock:
            build_tray_pinned_servers_mock.assert_called_once()
            build_start_app_minimized_mock.assert_called_once()
        else:
            build_tray_pinned_servers_mock.assert_not_called()
            build_start_app_minimized_mock.assert_not_called()


class TestTrayPinnedServersWidget:

    @patch("proton.vpn.app.gtk.widgets.headerbar.menu.settings.general_settings.get_setting")
    def test_build_populates_entry_when_being_initialized(self, get_setting_mock):
        get_setting_mock.return_value = ["PT", "CH"]
        psw = TrayPinnedServersWidget(Mock(), Mock())

        assert psw.entry.get_text() == "PT, CH"

    @patch("proton.vpn.app.gtk.widgets.headerbar.menu.settings.general_settings.save_setting")
    def test_save_setting_when_invoking_callback(self, save_setting_mock):
        with patch.object(EntryWidget, '__init__', return_value=None) as mock_parent_init:
            tray_indicator_mock = Mock()
            controller_mock = Mock()
            gtk_entry_mock = Mock()
            raw_text = "CH, PT"
            expected_format_when_passed_to_save_setting = ["CH", "PT"]
            gtk_entry_mock.get_text.return_value = raw_text

            psw = TrayPinnedServersWidget(controller_mock, tray_indicator_mock)

            callback = mock_parent_init.call_args[1]["callback"]
            callback(gtk_entry_mock, None, None)

            save_setting_mock.assert_called_once_with(
                controller_mock, psw.SETTING_NAME, expected_format_when_passed_to_save_setting
            )
            tray_indicator_mock.reload_pinned_servers.assert_called_once()
