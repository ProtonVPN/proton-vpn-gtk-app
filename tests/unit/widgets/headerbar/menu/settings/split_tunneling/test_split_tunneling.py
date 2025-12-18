from unittest.mock import Mock, patch
import pytest

from tests.unit.testing_utils import process_gtk_events

from proton.vpn.core.settings.split_tunneling import SplitTunnelingMode
from proton.vpn.app.gtk.widgets.headerbar.menu.settings.split_tunneling import SplitTunnelingToggle
from proton.vpn.app.gtk.widgets.headerbar.menu.settings.common import \
    UpgradePlusTag
from proton.vpn.app.gtk.controller import Controller


@pytest.fixture
def mock_controller():
    mock = Mock(name="controller", spec=Controller)
    mock.get_setting_attr.side_effect = [SplitTunnelingMode.EXCLUDE, ["test-app-exec"]]
    mock.user_tier = 1
    mock_controller.connection_disconnected = True

    return mock


def test_build_revealer_is_hides_app_list_when_setting_is_disabled(mock_controller):
    st = SplitTunnelingToggle(
        controller=mock_controller,
        setting_name="test.setting",
        enabled=False,
    )

    st.build_revealer()
    assert not st.revealer.get_child()


def test_build_revealer_shows_app_list_when_setting_is_enabled(mock_controller):
    st = SplitTunnelingToggle(
        controller=mock_controller,
        settings_container=None,
        setting_name="test.setting",
        enabled=True,
    )

    st.build_revealer()
    assert st.revealer.get_child()


def test_toggle_enabled_revealer_reveals_app_list(mock_controller):

    st = SplitTunnelingToggle(
        controller=mock_controller,
        settings_container=None,
        setting_name="test.setting",
        enabled=False,
        conflict_resolver=lambda setting_name, value: ""
    )

    st.build_revealer()
    st.switch.set_active(True)

    process_gtk_events()

    assert st.revealer.get_reveal_child()


def test_toggle_disable_revealer_hides_app_list(mock_controller):
    setting_name = "test.setting"

    st = SplitTunnelingToggle(
        controller=mock_controller,
        settings_container=None,
        setting_name=setting_name,
        enabled=True,
        conflict_resolver=lambda setting_name, value: ""
    )

    st.build_revealer()

    mock_controller.reset_mock()

    st.switch.set_active(False)

    process_gtk_events()

    mock_controller.save_setting_attr.assert_called_once_with(setting_name, False)
    assert not st.revealer.get_reveal_child()


def test_build_display_upgrade_tag_for_free_tier_user(mock_controller):
    mock_controller.user_tier = 0

    setting_name = "test.setting"

    st = SplitTunnelingToggle(
        controller=mock_controller,
        settings_container=None,
        setting_name=setting_name,
        enabled=True,
    )

    st.build_revealer()

    assert st.overridden_by_upgrade_tag


def test_settings_change_for_free_tier_user(mock_controller):
    mock_controller.user_tier = 0

    setting_name = "test.setting"

    st = SplitTunnelingToggle(
        controller=mock_controller,
        settings_container=None,
        setting_name=setting_name,
        enabled=True,
    )

    st.on_settings_changed(
        Mock(features=Mock(split_tunneling=Mock(enabled=True))))
