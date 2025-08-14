from unittest.mock import Mock
import pytest

from tests.unit.testing_utils import process_gtk_events

from proton.vpn.app.gtk.controller import Controller
from proton.vpn.core.settings.split_tunneling import SplitTunnelingMode
from proton.vpn.app.gtk.widgets.headerbar.menu.settings.split_tunneling.mode import (
    SplitTunnelingModeSetting, SETTINGS_PATH_NAME
)


@pytest.fixture
def mock_controller():
    mock = Mock(name="controller", spec=Controller)
    mock.get_setting_attr.return_value = SplitTunnelingMode.EXCLUDE
    mock.user_tier = 1
    mock_controller.connection_disconnected = True

    return mock


def test_split_tunneling_mode_setting_selects_exclude_radio_button_when_loading_with_exclude_mode(mock_controller):
    mode = SplitTunnelingModeSetting(controller=mock_controller)

    assert mode.get_exclude_radio_button().get_active()
    assert not mode.get_include_radio_button().get_active()


def test_split_tunneling_mode_signal_is_emitted_when_include_button_is_selected(
    mock_controller
):
    mock_callback = Mock(name="mode-switched-callback")
    mode = SplitTunnelingModeSetting(controller=mock_controller)

    mode.connect("mode-switched", mock_callback)

    mode.get_include_radio_button().set_active(True)

    process_gtk_events()

    mock_callback.assert_called_once_with(mode, SplitTunnelingMode.INCLUDE)


def test_split_tunneling_mode_setting_mode_is_saved_when_switching_from_exclude_to_include_mode(
    mock_controller
):
    mode = SplitTunnelingModeSetting(controller=mock_controller)

    mode.get_include_radio_button().set_active(True)

    process_gtk_events()

    mock_controller.save_setting_attr.assert_called_once_with(SETTINGS_PATH_NAME, SplitTunnelingMode.INCLUDE)
