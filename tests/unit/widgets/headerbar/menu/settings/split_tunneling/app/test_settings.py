from unittest.mock import Mock, patch

import pytest

from tests.unit.testing_utils import process_gtk_events

from proton.vpn.app.gtk.widgets.headerbar.menu.settings.split_tunneling.app.settings import \
    AppBasedSplitTunnelingSettings, LABEL_CONVERSION
from proton.vpn.app.gtk.widgets.headerbar.menu.settings.split_tunneling.app.selected_app_list \
    import SelectedAppList
from proton.vpn.app.gtk.controller import Controller
from proton.vpn.app.gtk.widgets.headerbar.menu.settings.split_tunneling.app.data_structures \
    import AppData
from proton.vpn.core.settings.split_tunneling import SplitTunnelingMode


from .mock_app_data import mock_app_native


@pytest.fixture
def mock_controller():
    return Mock(spec=Controller, name="controller")


@pytest.fixture
def mock_selected_app_list():
    yield Mock(spec=SelectedAppList, name="selected_app_list")


def test_remove_app_when_received_signal_app_removed(
    mock_controller, mock_selected_app_list, mock_app_native
):
    settings_path_name = "test.path"
    split_tunneling_mode = SplitTunnelingMode.EXCLUDE

    sp = AppBasedSplitTunnelingSettings(
        controller=mock_controller,
        setting_path_name=settings_path_name,
        mode=split_tunneling_mode,
        installed_apps=[mock_app_native],
        stored_apps=[mock_app_native.executable],
    )

    sp._emit_signal_app_removed(mock_app_native)

    process_gtk_events()

    mock_controller.save_setting_attr.assert_called_once_with(settings_path_name, [])
    assert sp.get_app_count_label() == f"{sp.SELECTED_APPS_COUNT_LABEL} ({sp.amount_of_selected_apps})"


def test_refresh_app_list_when_received_signal_app_list_refreshed(
    mock_controller, mock_selected_app_list, mock_app_native
):
    settings_path_name = "test.path"
    split_tunneling_mode = SplitTunnelingMode.EXCLUDE

    mock_app_data_list = [mock_app_native]

    sp = AppBasedSplitTunnelingSettings(
        controller=mock_controller,
        setting_path_name=settings_path_name,
        mode=SplitTunnelingMode.EXCLUDE,
        installed_apps=mock_app_data_list,
        stored_apps=[]
    )

    sp._emit_signal_app_list_refreshed(mock_app_data_list)

    mock_controller.save_setting_attr.assert_called_once_with(settings_path_name, [mock_app_native.executable])
    assert sp.get_app_count_label() == f"{sp.SELECTED_APPS_COUNT_LABEL} ({sp.amount_of_selected_apps})"

@patch(target="proton.vpn.app.gtk.widgets.headerbar.menu.settings.split_tunneling.app.settings.AppSelectionWindow", name="app_selection_window")
def test_receive_selected_apps_when_selecting_apps_from_app_selection_window(
    mock_app_selection_window,
    mock_controller, mock_app_native
):
    mock_app_selection_window_instance = Mock()
    mock_app_selection_window.return_value = mock_app_selection_window_instance

    settings_path_name = "test.path"
    sp = AppBasedSplitTunnelingSettings(
        controller=mock_controller,
        setting_path_name=settings_path_name,
        installed_apps=[mock_app_native],
        stored_apps=[]
    )

    sp._click_on_add_button()

    process_gtk_events()

    on_add_apps_to_list_callback = mock_app_selection_window_instance.connect.call_args_list[0][0][1]
    on_add_apps_to_list_callback(None, [mock_app_native])

    mock_controller.save_setting_attr.assert_called_once_with(settings_path_name, [mock_app_native.executable])
