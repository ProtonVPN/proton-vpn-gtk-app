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
from proton.vpn.app.gtk.widgets.headerbar.menu.settings.connection_settings import ConnectionSettings
from proton.vpn.app.gtk.widgets.headerbar.menu.settings.common import RECONNECT_MESSAGE


MockOpenVPNTCP = Mock()
MockOpenVPNTCP.cls.protocol = "openvpn-tcp"
MockOpenVPNTCP.cls.ui_protocol = "OpenVPN (TCP)"
MockOpenVPNUDP = Mock()
MockOpenVPNUDP.cls.protocol = "openvpn-udp"
MockOpenVPNUDP.cls.ui_protocol = "OpenVPN (UDP)"


FREE_TIER = 0
PLUS_TIER = 1


@pytest.fixture
def mocked_controller_and_protocol():
    controller_mock = Mock(name="controller")
    controller_mock.get_available_protocols.return_value = [MockOpenVPNTCP, MockOpenVPNUDP]

    property_mock = PropertyMock(name="protocol", return_value=MockOpenVPNTCP.cls.protocol)
    type(controller_mock.get_settings.return_value).protocol = property_mock

    return controller_mock, property_mock


@pytest.fixture
def mocked_controller_and_vpn_accelerator():
    controller_mock = Mock(name="controller")
    controller_mock.get_settings.return_value = Mock()

    property_mock = PropertyMock()
    type(controller_mock.get_settings.return_value.features).vpn_accelerator = property_mock

    return controller_mock, property_mock


@pytest.fixture
def mocked_controller_and_moderate_nat():
    controller_mock = Mock(name="controller")
    controller_mock.get_settings.return_value = Mock()

    property_mock = PropertyMock()
    type(controller_mock.get_settings.return_value.features).moderate_nat = property_mock

    user_tier_mock = PropertyMock(return_value=PLUS_TIER)
    type(controller_mock).user_tier = user_tier_mock

    return controller_mock, property_mock


def test_protocol_when_setting_is_called_upon_building_ui_elements(mocked_controller_and_protocol):
    controller_mock, protocol_mock = mocked_controller_and_protocol

    connection_settings = ConnectionSettings(controller_mock, Mock())
    connection_settings.build_protocol()

    protocol_mock.assert_called_once()


def test_protocol_when_combobox_is_set_to_initial_value(mocked_controller_and_protocol):
    controller_mock, protocol_mock = mocked_controller_and_protocol

    with patch("proton.vpn.app.gtk.widgets.headerbar.menu.settings.connection_settings.Gtk.ComboBoxText.set_active_id") as set_active_mock:
        connection_settings = ConnectionSettings(controller_mock, Mock())
        connection_settings.build_protocol()

        set_active_mock.assert_called_once_with(MockOpenVPNTCP.cls.protocol)


def test_protocol_when_switching_switch_protocol_and_ensure_changes_are_saved(mocked_controller_and_protocol):
    controller_mock, protocol_mock = mocked_controller_and_protocol
    connection_settings = ConnectionSettings(controller_mock, Mock())
    connection_settings.build_protocol()

    protocol_mock.reset_mock()

    connection_settings.protocol_row.interactive_object.set_active_id(MockOpenVPNUDP.cls.protocol)

    protocol_mock.assert_called_once_with(MockOpenVPNUDP.cls.protocol)
    controller_mock.save_settings.assert_called_once()


@pytest.mark.parametrize("is_connection_active", [False, True])    
def test_protocol_when_reconnect_message_reacts_accordingly_if_there_is_an_active_connection_or_not(is_connection_active, mocked_controller_and_protocol):
    controller_mock, protocol_mock = mocked_controller_and_protocol
    notification_bar_mock = Mock()

    controller_mock.is_connection_active = is_connection_active

    connection_settings = ConnectionSettings(controller_mock, notification_bar_mock)
    connection_settings.build_protocol()

    connection_settings.protocol_row.interactive_object.set_active_id(MockOpenVPNUDP.cls.protocol)

    if is_connection_active:
        notification_bar_mock.show_info_message.assert_called_once_with(RECONNECT_MESSAGE)
    else:
        notification_bar_mock.show_info_message.assert_not_called()


def test_protocol_when_connection_is_active_and_widget_is_not_interactive(mocked_controller_and_protocol):
    controller_mock, protocol_mock = mocked_controller_and_protocol
    notification_bar_mock = Mock()

    controller_mock.is_connection_disconnected = False

    connection_settings = ConnectionSettings(controller_mock, notification_bar_mock)
    connection_settings.build_protocol()

    assert not connection_settings.protocol_row.enabled


def test_vpn_accelerator_when_setting_is_called_upon_building_ui_elements(mocked_controller_and_vpn_accelerator):
    controller_mock, vpn_accelerator_mock = mocked_controller_and_vpn_accelerator

    connection_settings = ConnectionSettings(controller_mock, Mock())
    connection_settings.build_vpn_accelerator()

    vpn_accelerator_mock.assert_called_once()


@pytest.mark.parametrize("vpn_accelerator_enabled", [False, True])
def test_vpn_accelerator_when_switch_is_set_to_initial_value(vpn_accelerator_enabled, mocked_controller_and_vpn_accelerator):
    controller_mock, vpn_accelerator_mock = mocked_controller_and_vpn_accelerator

    vpn_accelerator_mock.return_value = vpn_accelerator_enabled

    with patch("proton.vpn.app.gtk.widgets.headerbar.menu.settings.connection_settings.Gtk.Switch.set_state") as set_state_mock:
        connection_settings = ConnectionSettings(controller_mock, Mock())
        connection_settings.build_vpn_accelerator()

        set_state_mock.assert_called_once_with(vpn_accelerator_enabled)


@pytest.mark.parametrize("vpn_accelerator_enabled", [False, True])
def test_vpn_accelerator_when_switching_switch_state_and_ensure_changes_are_saved(vpn_accelerator_enabled, mocked_controller_and_vpn_accelerator):
    controller_mock, vpn_accelerator_mock = mocked_controller_and_vpn_accelerator

    vpn_accelerator_mock.return_value = vpn_accelerator_enabled

    connection_settings = ConnectionSettings(controller_mock, Mock())
    connection_settings.build_vpn_accelerator()

    vpn_accelerator_mock.reset_mock()

    connection_settings.vpn_accelerator_row.interactive_object.set_state(not vpn_accelerator_enabled)

    vpn_accelerator_mock.assert_called_once_with(not vpn_accelerator_enabled)
    controller_mock.save_settings.assert_called_once()


@pytest.mark.parametrize("is_connection_active", [False, True])    
def test_vpn_accelerator_when_reconnect_message_reacts_accordingly_if_there_is_an_active_connection_or_not(is_connection_active, mocked_controller_and_vpn_accelerator):
    controller_mock, vpn_accelerator_mock = mocked_controller_and_vpn_accelerator
    notification_bar_mock = Mock()

    vpn_accelerator_mock.return_value = True
    controller_mock.is_connection_active = is_connection_active

    connection_settings = ConnectionSettings(controller_mock, notification_bar_mock)
    connection_settings.build_vpn_accelerator()

    connection_settings.vpn_accelerator_row.interactive_object.set_state(False)

    if is_connection_active:
        notification_bar_mock.show_info_message.assert_called_once_with(RECONNECT_MESSAGE)
    else:
        notification_bar_mock.show_info_message.assert_not_called()


def test_moderate_nat_when_setting_is_called_upon_building_ui_elements(mocked_controller_and_moderate_nat):
    controller_mock, moderate_nat_mock = mocked_controller_and_moderate_nat

    connection_settings = ConnectionSettings(controller_mock, Mock())
    connection_settings.build_moderate_nat()

    moderate_nat_mock.assert_called_once()


@pytest.mark.parametrize("moderate_nat_enabled", [False, True])
def test_moderate_nat_when_switch_is_set_to_initial_value(moderate_nat_enabled, mocked_controller_and_moderate_nat):
    controller_mock, moderate_nat_mock = mocked_controller_and_moderate_nat

    moderate_nat_mock.return_value = moderate_nat_enabled

    with patch("proton.vpn.app.gtk.widgets.headerbar.menu.settings.connection_settings.Gtk.Switch.set_state") as set_state_mock:
        connection_settings = ConnectionSettings(controller_mock, Mock())
        connection_settings.build_moderate_nat()

        set_state_mock.assert_called_once_with(moderate_nat_enabled)


@pytest.mark.parametrize("moderate_nat_enabled", [False, True])
def test_moderate_nat_when_switching_switch_state_and_ensure_changes_are_saved(moderate_nat_enabled, mocked_controller_and_moderate_nat):
    controller_mock, moderate_nat_mock = mocked_controller_and_moderate_nat

    moderate_nat_mock.return_value = moderate_nat_enabled

    connection_settings = ConnectionSettings(controller_mock, Mock())
    connection_settings.build_moderate_nat()

    moderate_nat_mock.reset_mock()

    connection_settings.moderate_nat_row.interactive_object.set_state(not moderate_nat_enabled)

    moderate_nat_mock.assert_called_once_with(not moderate_nat_enabled)
    controller_mock.save_settings.assert_called_once()


@pytest.mark.parametrize("is_connection_active", [False, True])    
def test_moderate_nat_when_reconnect_message_reacts_accordingly_if_there_is_an_active_connection_or_not(is_connection_active, mocked_controller_and_moderate_nat):
    controller_mock, moderate_nat_mock = mocked_controller_and_moderate_nat
    notification_bar_mock = Mock()
    
    moderate_nat_mock.return_value = True
    controller_mock.is_connection_active = is_connection_active

    connection_settings = ConnectionSettings(controller_mock, notification_bar_mock)
    connection_settings.build_moderate_nat()

    connection_settings.moderate_nat_row.interactive_object.set_state(False)

    if is_connection_active:
        notification_bar_mock.show_info_message.assert_called_once_with(RECONNECT_MESSAGE)
    else:
        notification_bar_mock.show_info_message.assert_not_called()


@pytest.mark.parametrize("user_tier", [FREE_TIER, PLUS_TIER])
def test_moderate_nat_upgrade_tag_override_interactive_object_if_plan_upgrade_is_required(user_tier, mocked_controller_and_moderate_nat):
    controller_mock, moderate_nat_mock = mocked_controller_and_moderate_nat

    user_tier_mock = PropertyMock(return_value=user_tier)
    type(controller_mock).user_tier = user_tier_mock

    feature_settings = ConnectionSettings(controller_mock, Mock())
    feature_settings.build_moderate_nat()

    if user_tier == FREE_TIER:
        assert feature_settings.moderate_nat_row.overridden_by_upgrade_tag
    else:
        assert not feature_settings.moderate_nat_row.overridden_by_upgrade_tag
