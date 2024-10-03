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
from tests.unit.testing_utils import process_gtk_events
from proton.vpn.app.gtk.widgets.headerbar.menu.settings.feature_settings import FeatureSettings, KillSwitchSettingEnum, KillSwitchWidget, ToggleWidget
from proton.vpn.core.settings import NetShield


FREE_TIER = 0
PLUS_TIER = 1

KILLSWITCH_STANDARD = 1
KILLSWITCH_ADVANCED = 2


@patch("proton.vpn.app.gtk.widgets.headerbar.menu.settings.feature_settings.FeatureSettings.pack_start")
@patch("proton.vpn.app.gtk.widgets.headerbar.menu.settings.feature_settings.ComboboxWidget")
def test_build_moderate_nat_save_new_value_when_callback_is_called(combobox_widget_mock, _):
    settings_window_mock = Mock()
    fs = FeatureSettings(MagicMock(), settings_window_mock)
    fs.build_netshield()
    new_value = "2"

    gtk_combobox_widget_mock = Mock()
    # We need to simulate the structure for a Gtk.ComboBoxText
    gtk_combobox_widget_mock.get_model.return_value = [[None, new_value]]
    gtk_combobox_widget_mock.get_active_iter.return_value = 0

    callback = combobox_widget_mock.call_args[1]["callback"]

    callback(gtk_combobox_widget_mock, combobox_widget_mock)
    combobox_widget_mock.save_setting.assert_called_once_with(int(new_value))
    settings_window_mock.notify_user_with_reconnect_message.assert_called_once()


@pytest.mark.parametrize("enabled", [False, True])
@patch("proton.vpn.app.gtk.widgets.headerbar.menu.settings.feature_settings.FeatureSettings.pack_start")
@patch("proton.vpn.app.gtk.widgets.headerbar.menu.settings.feature_settings.ToggleWidget")
def test_build_port_forwarding_updates_description_when_being_initialized_if_enabled(toggle_widget_mock, _, enabled):
    toggle_mock = Mock()
    toggle_mock.get_setting.return_value = enabled
    toggle_widget_mock.return_value = toggle_mock

    fs = FeatureSettings(MagicMock(), Mock())
    fs.build_port_forwarding()

    if enabled:
        toggle_mock.description.set_label.assert_called_once_with(fs.PORT_FORWARDING_SETUP_GUIDE)
    else:
        toggle_mock.description.set_label.assert_not_called()


@pytest.mark.parametrize("new_value", [False, True])
@patch("proton.vpn.app.gtk.widgets.headerbar.menu.settings.feature_settings.FeatureSettings.pack_start")
@patch("proton.vpn.app.gtk.widgets.headerbar.menu.settings.feature_settings.ToggleWidget")
def test_build_port_forwarding_save_new_value_when_callback_is_called(toggle_widget_mock, _, new_value):
    settings_window_mock = Mock()
    fs = FeatureSettings(MagicMock(), settings_window_mock)
    fs.build_port_forwarding()

    toggle_widget = toggle_widget_mock.call_args[1]
    callback = toggle_widget["callback"]

    callback(None, new_value, toggle_widget_mock)

    toggle_widget_mock.save_setting.assert_called_once_with(new_value)
    toggle_widget_mock.description.set_label.assert_called_once_with(
        fs.PORT_FORWARDING_SETUP_GUIDE if new_value else fs.PORT_FORWARDING_DESCRIPTION
    )
    settings_window_mock.notify_user_with_reconnect_message.assert_called_once()


class TestKillSwitchWidget:

    @patch("proton.vpn.app.gtk.widgets.headerbar.menu.settings.feature_settings.KillSwitchWidget.attach")
    @patch("proton.vpn.app.gtk.widgets.headerbar.menu.settings.feature_settings.ToggleWidget.save_setting")
    @patch("proton.vpn.app.gtk.widgets.headerbar.menu.settings.feature_settings.ToggleWidget.get_setting")
    def test_save_setting_when_switching_killswitch_from_disabled_to_enabled_and_revealer_is_shown(self, get_setting_mock, save_setting_mock, _):
        with patch.object(ToggleWidget, '__init__', return_value=None) as mock_parent_init:
            simulate_toggled_switch = True
            mock_gtk = Mock()
            mock_standard_radio_button = Mock()
            mock_advanced_radio_button = Mock()
            mock_revelear = Mock()
            mock_gtk.RadioButton.side_effect = [mock_standard_radio_button, mock_standard_radio_button]
            mock_gtk.Revealer.return_value = mock_revelear
            get_setting_mock.return_value = KillSwitchSettingEnum.OFF

            ks = KillSwitchWidget(Mock(), gtk=mock_gtk)
            ks.build_revealer()

            mock_standard_radio_button.reset_mock()
            mock_revelear.reset_mock()

            callback = mock_parent_init.call_args[1]["callback"]
            callback(None, True, simulate_toggled_switch)

            save_setting_mock.assert_called_once_with(KillSwitchSettingEnum.ON.value)
            mock_revelear.set_reveal_child.assert_called_once_with(True)
            mock_standard_radio_button.set_active.assert_called_once_with(True)

    @patch("proton.vpn.app.gtk.widgets.headerbar.menu.settings.feature_settings.KillSwitchWidget.attach")
    @patch("proton.vpn.app.gtk.widgets.headerbar.menu.settings.feature_settings.ToggleWidget.save_setting")
    @patch("proton.vpn.app.gtk.widgets.headerbar.menu.settings.feature_settings.ToggleWidget.get_setting")
    def test_save_setting_when_switching_killswitch_from_standard_to_advanced(self, get_setting_mock, save_setting_mock, _):
        mock_gtk = Mock()
        mock_standard_radio_button = Mock()
        mock_advanced_radio_button = Mock()
        mock_revelear = Mock()
        mock_gtk.RadioButton.side_effect = [mock_standard_radio_button, mock_advanced_radio_button]
        mock_gtk.Revealer.return_value = mock_revelear
        get_setting_mock.return_value = KillSwitchSettingEnum.ON

        ks = KillSwitchWidget(Mock(), gtk=mock_gtk)
        ks.build_revealer()
        mock_revelear.reset_mock()

        mock_advanced_radio_button_callback = mock_advanced_radio_button.connect.call_args[0][1]
        mock_advanced_radio_button.reset_mock()

        mock_revelear.get_reveal_child.return_value = True
        mock_advanced_radio_button.get_active.return_value = True

        mock_advanced_radio_button_callback(
            mock_advanced_radio_button, KillSwitchSettingEnum.PERMANENT.value
        )

        save_setting_mock.assert_called_once_with(KillSwitchSettingEnum.PERMANENT.value)

    @patch("proton.vpn.app.gtk.widgets.headerbar.menu.settings.feature_settings.KillSwitchWidget.attach")
    @patch("proton.vpn.app.gtk.widgets.headerbar.menu.settings.feature_settings.ToggleWidget.save_setting")
    @patch("proton.vpn.app.gtk.widgets.headerbar.menu.settings.feature_settings.ToggleWidget.get_setting")
    def test_save_setting_when_switching_killswitch_from_permanent_to_disabled_and_revealer_is_hidden(self, get_setting_mock, save_setting_mock, _):
        with patch.object(ToggleWidget, '__init__', return_value=None) as mock_parent_init:
            simulate_toggled_switch = True
            mock_gtk = Mock()
            mock_standard_radio_button = Mock()
            mock_advanced_radio_button = Mock()
            mock_revelear = Mock()
            mock_gtk.RadioButton.side_effect = [mock_standard_radio_button, mock_advanced_radio_button]
            mock_gtk.Revealer.return_value = mock_revelear
            get_setting_mock.return_value = KillSwitchSettingEnum.PERMANENT

            ks = KillSwitchWidget(Mock(), gtk=mock_gtk)
            ks.build_revealer()

            mock_revelear.reset_mock()
            mock_standard_radio_button.reset_mock()

            callback = mock_parent_init.call_args[1]["callback"]
            callback(None, False, simulate_toggled_switch)

            save_setting_mock.assert_called_once_with(KillSwitchSettingEnum.OFF.value)
            mock_revelear.set_reveal_child.assert_called_once_with(False)
            mock_standard_radio_button.set_active.assert_called_once_with(True)
