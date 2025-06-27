from unittest.mock import Mock, patch
import pytest

from tests.unit.testing_utils import process_gtk_events

from proton.vpn.app.gtk.widgets.headerbar.menu.settings.split_tunneling import SplitTunnelingToggle
from proton.vpn.app.gtk.controller import Controller


@pytest.fixture
def mock_controller():
    mock = Mock(name="controller", spec=Controller)
    mock.get_setting_attr.return_value = ["test-app-exec"]

    return mock


@patch(target="proton.vpn.app.gtk.widgets.headerbar.menu.settings.split_tunneling.split_tunneling.SplitTunnelingToggle.attach", autospec=True, name="mock_attach")
def test_build_revealer_is_hides_app_list_when_setting_is_disabled(_, mock_controller,):
    mock_settings_container = Mock(name="settings_container")

    st = SplitTunnelingToggle(
        controller=mock_controller,
        settings_container=mock_settings_container,
        setting_name="test.setting",
        enabled=False,
    )

    st.build_revealer()
    assert not st.revealer.get_child()


def test_build_revealer_shows_app_list_when_setting_is_enabled(mock_controller):
    mock_controller.user_tier = 1
    mock_controller.is_connection_disconnected = True
    mock_controller.get_setting_attr.return_value = ["test-app-exec"]

    st = SplitTunnelingToggle(
        controller=mock_controller,
        settings_container=None,
        setting_name="test.setting",
        enabled=True,
    )

    st.build_revealer()
    assert st.revealer.get_child()


def test_toggle_enabled_revealer_reveals_app_list(mock_controller):
    mock_controller.user_tier = 1
    mock_controller.is_connection_disconnected = True

    st = SplitTunnelingToggle(
        controller=mock_controller,
        settings_container=None,
        setting_name="test.setting",
        enabled=False,
    )

    st.build_revealer()
    st.switch.set_state(True)

    process_gtk_events()

    assert st.revealer.get_reveal_child()


def test_toggle_disable_revealer_hides_app_list(mock_controller):
    mock_controller.user_tier = 1
    mock_controller.is_connection_disconnected = True
    setting_name = "test.setting"

    st = SplitTunnelingToggle(
        controller=mock_controller,
        settings_container=None,
        setting_name=setting_name,
        enabled=True,
    )

    st.build_revealer()

    mock_controller.reset_mock()

    st.switch.set_state(False)

    process_gtk_events()

    mock_controller.save_setting_attr.assert_called_once_with(setting_name, False)
    assert not st.revealer.get_reveal_child()
