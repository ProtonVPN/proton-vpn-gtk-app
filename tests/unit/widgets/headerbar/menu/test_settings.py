import pytest
from unittest.mock import Mock, PropertyMock, patch
from tests.unit.testing_utils import process_gtk_events
from proton.vpn.app.gtk.widgets.headerbar.menu.settings import SettingsWindow, ConnectionSettings


@pytest.fixture
def mocked_objects():
    controller_mock = Mock(name="controller")
    settings_mock = Mock(name="settings")

    controller_mock.get_settings.return_value = settings_mock

    features_mock = Mock(name="features")
    type(settings_mock).features = features_mock

    yield controller_mock, features_mock



class TestSettingsWindow:

    def test_settings_window_ensure_passed_objects_are_added_to_container(self):
        connection_settings = Mock()
        notification_bar_mock = Mock()
        with patch("proton.vpn.app.gtk.widgets.headerbar.menu.settings.Gtk.Box.pack_start") as pack_start_mock:
            settings_window = SettingsWindow(Mock(), notification_bar_mock, connection_settings)

            assert pack_start_mock.mock_calls[0].args == (notification_bar_mock, False, False, 0)
            assert pack_start_mock.mock_calls[1].args == (connection_settings, False, False, 0)

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


class TestConnectionSettings:

    def test_vpn_accelerator_setting_is_called_when_building_ui(self, mocked_objects):
        controller_mock, features_mock = mocked_objects

        vpn_accelerator_mock = PropertyMock()
        type(features_mock).vpn_accelerator = vpn_accelerator_mock

        connection_settings = ConnectionSettings(controller_mock, Mock())
        connection_settings.build_ui()

        vpn_accelerator_mock.assert_called_once()

    @pytest.mark.parametrize("vpn_accelerator_enabled", [False, True])
    def test_vpn_accelerator_setting_switch_is_set_to_initial_value(self, vpn_accelerator_enabled, mocked_objects):
        controller_mock, features_mock = mocked_objects

        vpn_accelerator_mock = PropertyMock(return_value=vpn_accelerator_enabled)
        type(features_mock).vpn_accelerator = vpn_accelerator_mock

        with patch("proton.vpn.app.gtk.widgets.headerbar.menu.settings.Gtk.Switch.set_state") as set_state_mock:
            connection_settings = ConnectionSettings(controller_mock, Mock())
            connection_settings.build_ui()

            set_state_mock.assert_called_once_with(vpn_accelerator_enabled)

    @pytest.mark.parametrize("vpn_accelerator_enabled", [False, True])
    def test_vpn_accelerator_setting_when_switching_switch_state_and_changes_are_saved(self, vpn_accelerator_enabled, mocked_objects):
        controller_mock, features_mock = mocked_objects
        vpn_accelerator_mock = PropertyMock(return_value=vpn_accelerator_enabled)
        type(features_mock).vpn_accelerator = vpn_accelerator_mock

        connection_settings = ConnectionSettings(controller_mock, Mock())
        connection_settings.build_ui()

        vpn_accelerator_mock.reset_mock()

        connection_settings.vpn_accelerator_switch.set_state(not vpn_accelerator_enabled)

        vpn_accelerator_mock.assert_called_once_with(not vpn_accelerator_enabled)
        controller_mock.save_settings.assert_called_once()

    @pytest.mark.parametrize("is_connection_active", [False, True])    
    def test_vpn_accelerator_setting_reconnect_message_reacts_accordingly_if_there_is_an_active_connection_or_not(self, is_connection_active, mocked_objects):
        controller_mock, features_mock = mocked_objects
        notification_bar_mock = Mock()
        vpn_accelerator_mock = PropertyMock(return_value=True)
        type(features_mock).vpn_accelerator = vpn_accelerator_mock

        controller_mock.is_connection_active = is_connection_active

        connection_settings = ConnectionSettings(controller_mock, notification_bar_mock)
        connection_settings.build_ui()

        connection_settings.vpn_accelerator_switch.set_state(False)

        if is_connection_active:
            notification_bar_mock.show_info_message.assert_called_once_with(connection_settings.RECONNECT_MESSAGE)
        else:
            notification_bar_mock.show_info_message.assert_not_called()


