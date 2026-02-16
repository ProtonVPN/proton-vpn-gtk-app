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
from unittest.mock import Mock, patch, MagicMock
from tests.unit.testing_utils import process_gtk_events
from proton.vpn.app.gtk.widgets.headerbar.menu.settings.feature_settings import FeatureSettings, ToggleWidget
from proton.vpn.app.gtk.widgets.headerbar.menu.settings.kill_switch import KillSwitchSettingEnum, KillSwitchWidget
from proton.vpn.core.settings import NetShield


FREE_TIER = 0
PLUS_TIER = 1

KILLSWITCH_STANDARD = 1
KILLSWITCH_ADVANCED = 2

def test_build_moderate_nat_save_new_value_when_callback_is_called():
    controller_mock = Mock()
    controller_mock.user_tier = PLUS_TIER
    settings_window_mock = Mock()
    fs = FeatureSettings(controller_mock, settings_window_mock)
    fs.build_netshield()
    new_value = "2"

    combo_box_widget = fs.get_last_child()
    combo_box_widget.combobox.set_active_id(new_value)

    controller_mock.save_setting_attr.assert_called_once_with("settings.features.netshield", int(new_value))
    settings_window_mock.notify_user_with_reconnect_message.assert_not_called()


@pytest.mark.parametrize("new_value", [True, False])
def test_build_port_forwarding_save_new_value_when_callback_is_called(new_value):
    settings_window_mock = Mock()
    controller_mock = Mock()
    controller_mock.user_tier = PLUS_TIER
    controller_mock.get_setting_attr.return_value = not new_value
    fs = FeatureSettings(controller_mock, settings_window_mock)
    fs.build_port_forwarding()

    toggle_widget = fs.get_last_child()

    toggle_widget.switch.set_active(new_value)

    controller_mock.save_setting_attr.assert_called_once_with("settings.features.port_forwarding", new_value)
    settings_window_mock.notify_user_with_reconnect_message.assert_not_called()


class TestKillSwitchWidget:

    def test_save_setting_when_switching_killswitch_from_disabled_to_enabled_and_standard_radio_button_is_selected(self):
        controller = Mock()
        controller.get_setting_attr.return_value = KillSwitchSettingEnum.OFF.value

        ks = KillSwitchWidget(controller, conflict_resolver=lambda setting_name, value: "")
        ks.build_revealer()

        ks.switch.set_active(True)

        # TODO: the setting is saved twice: first when enabling the toggle and then when enabling the standard ks radio button
        controller.save_setting_attr.assert_called_with("settings.killswitch", KillSwitchSettingEnum.ON.value)
        assert ks.standard_radio_button.get_active()

    def test_save_setting_when_switching_killswitch_from_standard_to_advanced(self):
        controller = Mock()
        controller.get_setting_attr.return_value = KillSwitchSettingEnum.ON.value

        ks = KillSwitchWidget(controller, conflict_resolver=lambda setting_name, value: "")
        ks.build_revealer()

        ks.advanced_radio_button.set_active(True)

        controller.save_setting_attr.assert_called_once_with("settings.killswitch", KillSwitchSettingEnum.PERMANENT.value)

    def test_save_setting_when_switching_killswitch_from_permanent_to_disabled(self):
        controller = Mock()
        controller.get_setting_attr.return_value = KillSwitchSettingEnum.PERMANENT.value

        ks = KillSwitchWidget(controller, conflict_resolver=lambda setting_name, value: "")
        ks.build_revealer()

        ks.switch.set_active(False)

        controller.save_setting_attr.assert_called_once_with("settings.killswitch", KillSwitchSettingEnum.OFF.value)
        assert not ks.advanced_radio_button.get_active()


class TestNetshield:

    @pytest.mark.parametrize("response_type", [-8, -9])
    @patch("proton.vpn.app.gtk.widgets.headerbar.menu.settings.feature_settings.ConfirmationDialog")
    @patch("proton.vpn.app.gtk.widgets.headerbar.menu.settings.feature_settings.ComboboxWidget.off")
    @patch("proton.vpn.app.gtk.widgets.headerbar.menu.settings.feature_settings.ComboboxWidget.get_setting")
    def test_disable_netshield_and_prompt_user_via_dialog_when_enabling_custom_dns_while_netshield_is_enabled_and_ensure_that_either_custom_dns_or_netshield_is_disabled(self, get_setting_mock, netshield_off_mock, confirmation_dialog_mock, response_type):
        get_setting_mock.return_value = str(NetShield.BLOCK_ADS_AND_TRACKING.value)
        controller_mock = Mock(name="controller_mock")
        controller_mock.user_tier = PLUS_TIER
        settings_window_mock = Mock(name="settings_window_mock")
        custom_dns_widget_mock = Mock(name="custom_dns_widget_mock")
        confirmation_dialog_instance_mock = Mock(name="confirmation_dialog_instance_mock")
        confirmation_dialog_mock.return_value = confirmation_dialog_instance_mock

        feature_settings = FeatureSettings(controller=controller_mock, settings_window=settings_window_mock)
        feature_settings.build_netshield()

        feature_settings.on_custom_dns_setting_changed(
            custom_dns_widget=custom_dns_widget_mock, custom_dns_enabled=True
        )

        on_dialog_button_click_callback = confirmation_dialog_instance_mock.connect.call_args[0][1]
        on_dialog_button_click_callback(confirmation_dialog_instance_mock, response_type)

        # -8: Gtk.ResponseType.YES
        # -9: Gtk.ResponseType.NO
        Gtk_ResponseType_YES = -8

        if response_type == Gtk_ResponseType_YES:
            netshield_off_mock.assert_called_once()
            custom_dns_widget_mock.off.assert_not_called()
        else:
            netshield_off_mock.assert_not_called()
            custom_dns_widget_mock.off.assert_called_once()

    @patch("proton.vpn.app.gtk.widgets.headerbar.menu.settings.feature_settings.ConfirmationDialog")
    @patch("proton.vpn.app.gtk.widgets.headerbar.menu.settings.feature_settings.ComboboxWidget.get_setting")
    def test_netshield_prompt_is_not_shown_to_the_user_when_netshield_is_disabled_while_enabling_custom_dns(self, get_setting_mock, confirmation_dialog_mock):
        get_setting_mock.return_value = str(NetShield.NO_BLOCK.value)
        controller_mock = Mock(name="controller_mock")
        controller_mock.user_tier = PLUS_TIER
        settings_window_mock = Mock(name="settings_window_mock")
        custom_dns_widget_mock = Mock(name="custom_dns_widget_mock")
        confirmation_dialog_instance_mock = Mock(name="confirmation_dialog_instance_mock")
        confirmation_dialog_mock.return_value = confirmation_dialog_instance_mock

        feature_settings = FeatureSettings(controller=controller_mock, settings_window=settings_window_mock)
        feature_settings.build_netshield()

        feature_settings.on_custom_dns_setting_changed(custom_dns_widget_mock, True)

        confirmation_dialog_mock.assert_not_called()
