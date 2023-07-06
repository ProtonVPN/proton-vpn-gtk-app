import pytest
from unittest.mock import Mock, PropertyMock, patch
from tests.unit.testing_utils import process_gtk_events
from proton.vpn.app.gtk.widgets.headerbar.menu.settings import SettingsWindow, ConnectionSettings, FeatureSettings, RECONNECT_MESSAGE, UpgradePlusTag
from proton.vpn.core_api.settings import NetShield


class TestSettingsWindow:

    def test_settings_window_ensure_passed_objects_are_added_to_container(self):
        feature_settings_mock = Mock()
        connection_settings_mock = Mock()
        notification_bar_mock = Mock()
        with patch("proton.vpn.app.gtk.widgets.headerbar.menu.settings.Gtk.Box.pack_start") as pack_start_mock:
            settings_window = SettingsWindow(Mock(), notification_bar_mock, feature_settings_mock, connection_settings_mock)

            assert pack_start_mock.mock_calls[0].args == (feature_settings_mock, False, False, 0)
            assert pack_start_mock.mock_calls[1].args == (connection_settings_mock, False, False, 0)
            assert pack_start_mock.mock_calls[2].args == (notification_bar_mock, False, False, 0)

    @pytest.mark.parametrize("present_window", [False, True])
    def test_settings_window_ensure_window_does_not_load_content_until_required(self, present_window):
        connection_settings = Mock()
        with patch("proton.vpn.app.gtk.widgets.headerbar.menu.settings.Gtk.Box.pack_start") as pack_start_mock:
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

        with patch("proton.vpn.app.gtk.widgets.headerbar.menu.settings.Gtk.ComboBoxText.set_active_id") as set_active_mock:
            feature_settings = FeatureSettings(controller_mock, Mock())
            feature_settings.build_netshield()

            set_active_mock.assert_called_once_with(str(netshield_option))

    def test_netshield_when_switching_switch_protocol_and_ensure_changes_are_saved(self, mocked_controller_and_netshield):
        controller_mock, netshield_mock = mocked_controller_and_netshield
        netshield_mock.return_value = NetShield.NO_BLOCK.value
        feature_settings = FeatureSettings(controller_mock, Mock())
        feature_settings.build_netshield()

        netshield_mock.reset_mock()

        feature_settings.netshield_combobox.set_active_id(str(NetShield.BLOCK_MALICIOUS_URL.value))

        netshield_mock.assert_called_once_with(NetShield.BLOCK_MALICIOUS_URL.value)
        controller_mock.save_settings.assert_called_once()

    @pytest.mark.parametrize("is_connection_active", [False, True])    
    def test_netshield_when_reconnect_message_reacts_accordingly_if_there_is_an_active_connection_or_not(self, is_connection_active, mocked_controller_and_netshield):
        controller_mock, netshield_mock = mocked_controller_and_netshield
        notification_bar_mock = Mock()

        controller_mock.is_connection_active = is_connection_active

        feature_settings = FeatureSettings(controller_mock, notification_bar_mock)
        feature_settings.build_netshield()

        feature_settings.netshield_combobox.set_active_id(str(NetShield.BLOCK_MALICIOUS_URL.value))

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

        feature_settings = FeatureSettings(controller_mock, Mock())
        feature_settings.build_netshield()

        assert feature_settings.netshield_row.get_property("sensitive") == is_client_config_netshield_enabled


DUMMY_PROTOCOL = "dummy-protocol"
DUMMY_PROTOCOL2 = "dummy-protocol2"


@pytest.fixture
def mocked_controller_and_protocol():
    controller_mock = Mock(name="controller")
    controller_mock.get_available_protocols.return_value = [DUMMY_PROTOCOL, DUMMY_PROTOCOL2]

    property_mock = PropertyMock(return_value=DUMMY_PROTOCOL)
    type(controller_mock.get_settings.return_value).protocol = property_mock

    return controller_mock, property_mock


@pytest.fixture
def mocked_controller_and_vpn_accelerator():
    controller_mock = Mock(name="controller")
    controller_mock.get_settings.return_value = Mock()

    property_mock = PropertyMock()
    type(controller_mock.get_settings.return_value.features).vpn_accelerator = property_mock

    return controller_mock, property_mock


class TestConnectionSettings:

    def test_protocol_when_setting_is_called_upon_building_ui_elements(self, mocked_controller_and_protocol):
        controller_mock, protocol_mock = mocked_controller_and_protocol

        connection_settings = ConnectionSettings(controller_mock, Mock())
        connection_settings.build_protocol()

        protocol_mock.assert_called_once()

    def test_protocol_when_combobox_is_set_to_initial_value(self, mocked_controller_and_protocol):
        controller_mock, protocol_mock = mocked_controller_and_protocol

        with patch("proton.vpn.app.gtk.widgets.headerbar.menu.settings.Gtk.ComboBoxText.set_active_id") as set_active_mock:
            connection_settings = ConnectionSettings(controller_mock, Mock())
            connection_settings.build_protocol()

            set_active_mock.assert_called_once_with(DUMMY_PROTOCOL)

    def test_protocol_when_switching_switch_protocol_and_ensure_changes_are_saved(self, mocked_controller_and_protocol):
        controller_mock, protocol_mock = mocked_controller_and_protocol
        connection_settings = ConnectionSettings(controller_mock, Mock())
        connection_settings.build_protocol()

        protocol_mock.reset_mock()

        connection_settings.protocol_combobox.set_active_id(DUMMY_PROTOCOL2)

        protocol_mock.assert_called_once_with(DUMMY_PROTOCOL2)
        controller_mock.save_settings.assert_called_once()

    @pytest.mark.parametrize("is_connection_active", [False, True])    
    def test_protocol_when_reconnect_message_reacts_accordingly_if_there_is_an_active_connection_or_not(self, is_connection_active, mocked_controller_and_protocol):
        controller_mock, protocol_mock = mocked_controller_and_protocol
        notification_bar_mock = Mock()

        controller_mock.is_connection_active = is_connection_active

        connection_settings = ConnectionSettings(controller_mock, notification_bar_mock)
        connection_settings.build_protocol()

        connection_settings.protocol_combobox.set_active_id(DUMMY_PROTOCOL2)

        if is_connection_active:
            notification_bar_mock.show_info_message.assert_called_once_with(RECONNECT_MESSAGE)
        else:
            notification_bar_mock.show_info_message.assert_not_called()

    def test_vpn_accelerator_when_setting_is_called_upon_building_ui_elements(self, mocked_controller_and_vpn_accelerator):
        controller_mock, vpn_accelerator_mock = mocked_controller_and_vpn_accelerator

        connection_settings = ConnectionSettings(controller_mock, Mock())
        connection_settings.build_vpn_accelerator()

        vpn_accelerator_mock.assert_called_once()

    @pytest.mark.parametrize("vpn_accelerator_enabled", [False, True])
    def test_vpn_accelerator_when_switch_is_set_to_initial_value(self, vpn_accelerator_enabled, mocked_controller_and_vpn_accelerator):
        controller_mock, vpn_accelerator_mock = mocked_controller_and_vpn_accelerator

        vpn_accelerator_mock.return_value = vpn_accelerator_enabled

        with patch("proton.vpn.app.gtk.widgets.headerbar.menu.settings.Gtk.Switch.set_state") as set_state_mock:
            connection_settings = ConnectionSettings(controller_mock, Mock())
            connection_settings.build_vpn_accelerator()

            set_state_mock.assert_called_once_with(vpn_accelerator_enabled)

    @pytest.mark.parametrize("vpn_accelerator_enabled", [False, True])
    def test_vpn_accelerator_when_switching_switch_state_and_ensure_changes_are_saved(self, vpn_accelerator_enabled, mocked_controller_and_vpn_accelerator):
        controller_mock, vpn_accelerator_mock = mocked_controller_and_vpn_accelerator

        vpn_accelerator_mock.return_value = vpn_accelerator_enabled

        connection_settings = ConnectionSettings(controller_mock, Mock())
        connection_settings.build_vpn_accelerator()

        vpn_accelerator_mock.reset_mock()

        connection_settings.vpn_accelerator_switch.set_state(not vpn_accelerator_enabled)

        vpn_accelerator_mock.assert_called_once_with(not vpn_accelerator_enabled)
        controller_mock.save_settings.assert_called_once()

    @pytest.mark.parametrize("is_client_config_vpn_accelerator_enabled", [True, False])
    def test_vpn_accelerator_when_clientconfig_dictates_the_setting_state(self, is_client_config_vpn_accelerator_enabled, mocked_controller_and_vpn_accelerator):
        """The endpoint /clientconfig lets each client know if certain features are supported by the servers of not and thus should be respected.
        If a feature is disabled then we shouldn't be passing it to the servers."""

        controller_mock, vpn_accelerator_mock = mocked_controller_and_vpn_accelerator

        feature_flag_vpn_accelerator_mock = PropertyMock(return_value=is_client_config_vpn_accelerator_enabled)
        type(controller_mock.vpn_data_refresher.client_config.feature_flags).vpn_accelerator = feature_flag_vpn_accelerator_mock

        connection_settings = ConnectionSettings(controller_mock, Mock())
        connection_settings.build_vpn_accelerator()

        assert connection_settings.vpn_accelerator_row.get_property("sensitive") == is_client_config_vpn_accelerator_enabled


    @pytest.mark.parametrize("is_connection_active", [False, True])    
    def test_vpn_accelerator_when_reconnect_message_reacts_accordingly_if_there_is_an_active_connection_or_not(self, is_connection_active, mocked_controller_and_vpn_accelerator):
        controller_mock, vpn_accelerator_mock = mocked_controller_and_vpn_accelerator
        notification_bar_mock = Mock()
        
        vpn_accelerator_mock.return_value = True
        controller_mock.is_connection_active = is_connection_active

        connection_settings = ConnectionSettings(controller_mock, notification_bar_mock)
        connection_settings.build_vpn_accelerator()

        connection_settings.vpn_accelerator_switch.set_state(False)

        if is_connection_active:
            notification_bar_mock.show_info_message.assert_called_once_with(RECONNECT_MESSAGE)
        else:
            notification_bar_mock.show_info_message.assert_not_called()


@patch("proton.vpn.app.gtk.widgets.headerbar.menu.settings.Gdk")
def test_upgrade_plus_tag_displays_url_in_window(gdk_mock):
    gdk_mock.CURRENT_TIME = "mock-time"
    with patch("proton.vpn.app.gtk.widgets.headerbar.menu.settings.Gtk.show_uri_on_window") as show_in_browser:
        plus_tag = UpgradePlusTag()
        plus_tag.clicked()
        show_in_browser.assert_called_once_with(None, plus_tag.URL, gdk_mock.CURRENT_TIME)

