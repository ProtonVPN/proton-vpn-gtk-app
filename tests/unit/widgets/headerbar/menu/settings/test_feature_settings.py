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
from proton.vpn.app.gtk.widgets.headerbar.menu.settings.feature_settings import FeatureSettings
from proton.vpn.app.gtk.widgets.headerbar.menu.settings.common import RECONNECT_MESSAGE
from proton.vpn.core_api.settings import NetShield


FREE_TIER = 0
PLUS_TIER = 1


@pytest.fixture
def mocked_controller_and_netshield():
    controller_mock = Mock(name="controller")

    setting_property_mock = PropertyMock()
    type(controller_mock.get_settings.return_value.features).netshield = setting_property_mock

    user_tier_mock = PropertyMock(return_value=PLUS_TIER)
    type(controller_mock).user_tier = user_tier_mock

    return controller_mock, setting_property_mock


@pytest.fixture
def mocked_controller_and_port_forwarding():
    controller_mock = Mock(name="controller")
    controller_mock.get_settings.return_value = Mock()

    property_mock = PropertyMock()
    type(controller_mock.get_settings.return_value.features).port_forwarding = property_mock

    user_tier_mock = PropertyMock(return_value=PLUS_TIER)
    type(controller_mock).user_tier = user_tier_mock

    return controller_mock, property_mock


class TestFeatureSettings:

    def test_netshield_when_setting_is_called_upon_building_ui_elements(self, mocked_controller_and_netshield):
        controller_mock, netshield_mock = mocked_controller_and_netshield
        feature_settings = FeatureSettings(controller_mock, Mock())
        feature_settings.build_netshield()

        netshield_mock.assert_called_once()

    def test_netshield_when_combobox_is_set_to_initial_value(self, mocked_controller_and_netshield):
        controller_mock, netshield_mock = mocked_controller_and_netshield

        netshield_option = NetShield.BLOCK_MALICIOUS_URL.value
        netshield_mock.return_value = netshield_option

        with patch("proton.vpn.app.gtk.widgets.headerbar.menu.settings.feature_settings.Gtk.ComboBoxText.set_active_id") as set_active_mock:
            feature_settings = FeatureSettings(controller_mock, Mock())
            feature_settings.build_netshield()

            set_active_mock.assert_called_once_with(str(netshield_option))

    def test_netshield_when_switching_switch_protocol_and_ensure_changes_are_saved(self, mocked_controller_and_netshield):
        controller_mock, netshield_mock = mocked_controller_and_netshield
        netshield_mock.return_value = NetShield.NO_BLOCK.value
        feature_settings = FeatureSettings(controller_mock, Mock())
        feature_settings.build_netshield()

        netshield_mock.reset_mock()

        feature_settings.netshield_row.interactive_object.set_active_id(str(NetShield.BLOCK_MALICIOUS_URL.value))

        netshield_mock.assert_called_once_with(NetShield.BLOCK_MALICIOUS_URL.value)
        controller_mock.save_settings.assert_called_once()

    @pytest.mark.parametrize("is_connection_active", [False, True])    
    def test_netshield_when_reconnect_message_reacts_accordingly_if_there_is_an_active_connection_or_not(self, is_connection_active, mocked_controller_and_netshield):
        controller_mock, netshield_mock = mocked_controller_and_netshield
        notification_bar_mock = Mock()

        controller_mock.is_connection_active = is_connection_active

        feature_settings = FeatureSettings(controller_mock, notification_bar_mock)
        feature_settings.build_netshield()

        feature_settings.netshield_row.interactive_object.set_active_id(str(NetShield.BLOCK_MALICIOUS_URL.value))

        if is_connection_active:
            notification_bar_mock.show_info_message.assert_called_once_with(RECONNECT_MESSAGE)
        else:
            notification_bar_mock.show_info_message.assert_not_called()

    @pytest.mark.parametrize("user_tier", [FREE_TIER, PLUS_TIER])
    def test_netshield_upgrade_tag_override_interactive_object_if_plan_upgrade_is_required(self, user_tier, mocked_controller_and_netshield):
        controller_mock, netshield_mock = mocked_controller_and_netshield
        user_tier_mock = PropertyMock(return_value=user_tier)
        type(controller_mock).user_tier = user_tier_mock

        feature_settings = FeatureSettings(controller_mock, Mock())
        feature_settings.build_netshield()

        if user_tier == FREE_TIER:
            assert feature_settings.netshield_row.overriden_by_upgrade_tag
        else:
            assert not feature_settings.netshield_row.overriden_by_upgrade_tag


    @pytest.mark.parametrize("is_client_config_netshield_enabled", [True, False])
    def test_netshield_when_clientconfig_dictates_the_setting_state(self, is_client_config_netshield_enabled, mocked_controller_and_netshield):
        """The endpoint /clientconfig lets each client know if certain features are supported by the servers of not and thus should be respected.
        If a feature is disabled then we shouldn't be passing it to the servers."""
        controller_mock, netshield_mock = mocked_controller_and_netshield

        client_config_property_mock = PropertyMock(return_value=is_client_config_netshield_enabled)
        type(controller_mock.vpn_data_refresher.client_config.feature_flags).netshield = client_config_property_mock

        netshield_mock = PropertyMock(return_value=NetShield.BLOCK_MALICIOUS_URL.value)
        type(controller_mock.get_settings.return_value.features).netshield = netshield_mock

        feature_settings = FeatureSettings(controller_mock, Mock())
        feature_settings.build_netshield()

        if is_client_config_netshield_enabled:
            netshield_mock.call_count == 1
            assert feature_settings.netshield_row
        else:
            assert netshield_mock.call_args_list[1].args[0] == NetShield.NO_BLOCK.value
            assert not feature_settings.netshield_row

    def test_port_forwarding_when_setting_is_called_upon_building_ui_elements(self, mocked_controller_and_port_forwarding):
        controller_mock, port_forwarding_mock = mocked_controller_and_port_forwarding

        feature_settings = FeatureSettings(controller_mock, Mock())
        feature_settings.build_port_forwarding()

        port_forwarding_mock.assert_called_once()

    @pytest.mark.parametrize("port_forwarding_enabled", [False, True])
    def test_port_forwarding_when_switch_is_set_to_initial_value(self, port_forwarding_enabled, mocked_controller_and_port_forwarding):
        controller_mock, port_forwarding_mock = mocked_controller_and_port_forwarding

        port_forwarding_mock.return_value = port_forwarding_enabled

        with patch("proton.vpn.app.gtk.widgets.headerbar.menu.settings.feature_settings.Gtk.Switch.set_state") as set_state_mock:
            feature_settings = FeatureSettings(controller_mock, Mock())
            feature_settings.build_port_forwarding()

            set_state_mock.assert_called_once_with(port_forwarding_enabled)
        
    @pytest.mark.parametrize("is_port_forwarding_enabled", [True, False])
    def test_port_forwarding_when_switch_is_set_to_initial_value_and_description_is_displayed_accordingly(self, is_port_forwarding_enabled, mocked_controller_and_port_forwarding):
        controller_mock, port_forwarding_mock = mocked_controller_and_port_forwarding

        port_forwarding_mock.return_value = is_port_forwarding_enabled

        feature_settings = FeatureSettings(controller_mock, Mock())
        feature_settings.build_port_forwarding()

        if is_port_forwarding_enabled:
            assert feature_settings.port_forwarding_row.description.get_label() != feature_settings.PORT_FORWARDING_DESCRIPTION
        else:
            assert feature_settings.port_forwarding_row.description.get_label() == feature_settings.PORT_FORWARDING_DESCRIPTION

    @pytest.mark.parametrize("is_port_forwarding_enabled", [False, True])
    def test_port_forwarding_when_switching_switch_state_and_ensure_changes_are_saved(self, is_port_forwarding_enabled, mocked_controller_and_port_forwarding):
        controller_mock, port_forwarding_mock = mocked_controller_and_port_forwarding

        port_forwarding_mock.return_value = is_port_forwarding_enabled

        feature_settings = FeatureSettings(controller_mock, Mock())
        feature_settings.build_port_forwarding()

        port_forwarding_mock.reset_mock()

        feature_settings.port_forwarding_row.interactive_object.set_state(not is_port_forwarding_enabled)

        port_forwarding_mock.assert_called_once_with(not is_port_forwarding_enabled)
        controller_mock.save_settings.assert_called_once()

    @pytest.mark.parametrize("is_port_forwarding_enabled", [False, True])
    def test_port_forwarding_when_switching_switch_state_and_description_is_updated(self, is_port_forwarding_enabled, mocked_controller_and_port_forwarding):
        controller_mock, port_forwarding_mock = mocked_controller_and_port_forwarding

        port_forwarding_mock.return_value = is_port_forwarding_enabled

        feature_settings = FeatureSettings(controller_mock, Mock())
        feature_settings.build_port_forwarding()

        port_forwarding_mock.reset_mock()

        feature_settings.port_forwarding_row.interactive_object.set_state(not is_port_forwarding_enabled)

        if not is_port_forwarding_enabled:
            assert feature_settings.port_forwarding_row.description.get_label() != feature_settings.PORT_FORWARDING_DESCRIPTION
        else:
            assert feature_settings.port_forwarding_row.description.get_label() == feature_settings.PORT_FORWARDING_DESCRIPTION

    @pytest.mark.parametrize("is_client_config_port_forwarding_enabled", [True, False])
    def test_port_forwarding_when_clientconfig_dictates_the_setting_state(self, is_client_config_port_forwarding_enabled, mocked_controller_and_port_forwarding):
        """The endpoint /clientconfig lets each client know if certain features are supported by the servers of not and thus should be respected.
        If a feature is disabled then we shouldn't be passing it to the servers."""

        controller_mock, port_forwarding_mock = mocked_controller_and_port_forwarding

        feature_flag_port_forwarding_mock = PropertyMock(return_value=is_client_config_port_forwarding_enabled)
        type(controller_mock.vpn_data_refresher.client_config.feature_flags).port_forwarding = feature_flag_port_forwarding_mock

        port_forwarding_mock = PropertyMock(return_value=True)
        type(controller_mock.get_settings.return_value.features).port_forwarding = port_forwarding_mock

        feature_settings = FeatureSettings(controller_mock, Mock())
        feature_settings.build_port_forwarding()

        if is_client_config_port_forwarding_enabled:
            port_forwarding_mock.call_count == 1
            assert feature_settings.port_forwarding_row
        else:
            assert port_forwarding_mock.call_args_list[1].args[0] == is_client_config_port_forwarding_enabled
            assert not feature_settings.port_forwarding_row

    @pytest.mark.parametrize("is_connection_active", [False, True])    
    def test_port_forwarding_when_reconnect_message_reacts_accordingly_if_there_is_an_active_connection_or_not(self, is_connection_active, mocked_controller_and_port_forwarding):
        controller_mock, port_forwarding_mock = mocked_controller_and_port_forwarding
        notification_bar_mock = Mock()
        
        port_forwarding_mock.return_value = True
        controller_mock.is_connection_active = is_connection_active

        feature_settings = FeatureSettings(controller_mock, notification_bar_mock)
        feature_settings.build_port_forwarding()

        feature_settings.port_forwarding_row.interactive_object.set_state(False)

        if is_connection_active:
            notification_bar_mock.show_info_message.assert_called_once_with(RECONNECT_MESSAGE)
        else:
            notification_bar_mock.show_info_message.assert_not_called()

    @pytest.mark.parametrize("user_tier", [FREE_TIER, PLUS_TIER])
    def test_port_forwarding_upgrade_tag_override_interactive_object_if_plan_upgrade_is_required(self, user_tier, mocked_controller_and_port_forwarding):
        controller_mock, port_forwarding_mock = mocked_controller_and_port_forwarding
        user_tier_mock = PropertyMock(return_value=user_tier)
        type(controller_mock).user_tier = user_tier_mock

        feature_settings = FeatureSettings(controller_mock, Mock())
        feature_settings.build_port_forwarding()

        if user_tier == FREE_TIER:
            assert feature_settings.port_forwarding_row.overriden_by_upgrade_tag
        else:
            assert not feature_settings.port_forwarding_row.overriden_by_upgrade_tag
        