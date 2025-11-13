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


from .mock_app_data import mock_app_data


@pytest.fixture
def mock_controller():
    return Mock(spec=Controller, name="controller")


@pytest.fixture
def mock_selected_app_list():
    yield Mock(spec=SelectedAppList, name="selected_app_list")


def test_app_based_split_tunneling_saves_modified_list_after_receiving_app_removed_signal(
    mock_controller, mock_app_data
):
    settings_path_name = "test.path"
    split_tunneling_mode = SplitTunnelingMode.EXCLUDE

    sp = AppBasedSplitTunnelingSettings(
        controller=mock_controller,
        setting_path_name_template=settings_path_name,
        mode=split_tunneling_mode,
        installed_apps=[mock_app_data],
        stored_apps=[mock_app_data.executable],
    )

    sp.emit_signal_app_removed(mock_app_data)

    process_gtk_events()

    mock_controller.save_setting_attr.assert_called_once_with(settings_path_name, [])
    assert sp.get_app_count_label() == f"({sp.amount_of_selected_apps})"


def test_app_based_split_tunneling_saves_modified_list_after_receiving_app_list_refreshed_signal(
    mock_controller, mock_app_data
):
    settings_path_name = "test.path"

    mock_app_data_list = [mock_app_data]

    sp = AppBasedSplitTunnelingSettings(
        controller=mock_controller,
        setting_path_name_template=settings_path_name,
        mode=SplitTunnelingMode.EXCLUDE,
        installed_apps=mock_app_data_list,
        stored_apps=[]
    )

    sp.emit_signal_app_list_refreshed(mock_app_data_list)

    mock_controller.save_setting_attr.assert_called_once_with(settings_path_name, [mock_app_data.executable])
    assert sp.get_app_count_label() == f"({sp.amount_of_selected_apps})"


def test_app_based_split_tunneling_settings_restores_app_list_when_st_mode_is_changed(
    mock_controller
):
    include_app = AppData(
        name="test-app",
        executable="test/path/include",
        icon_name="test-icon"
    )
    exclude_app = AppData(
        name="test-app",
        executable="test/path/exclude",
        icon_name="test-icon"
    )

    settings_path_name = "test.path"
    mock_controller.get_setting_attr.side_effect = [["test/path/include"], ["test/path/exclude"]]

    mock_app_data_list = [include_app, exclude_app]

    sp = AppBasedSplitTunnelingSettings(
        controller=mock_controller,
        setting_path_name_template=settings_path_name,
        mode=SplitTunnelingMode.EXCLUDE,
        installed_apps=mock_app_data_list,
        stored_apps=[],
    )
    sp.update_list_on_new_mode(mode=SplitTunnelingMode.INCLUDE)

    mock_controller.save_setting_attr.assert_called_once_with(settings_path_name, [include_app.executable])
