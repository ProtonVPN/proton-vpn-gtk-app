from unittest.mock import Mock


from tests.unit.testing_utils import process_gtk_events

from proton.vpn.app.gtk.widgets.headerbar.menu.settings.split_tunneling.app.selected_app_list \
    import SelectedAppList

from .mock_app_data import mock_app_data


def test_remove_app_is_removed_and_signal_is_emitted_when_app_is_removed_from_list(mock_app_data):
    mock_app_removed_callback = Mock()
    sap = SelectedAppList(apps_to_add=[mock_app_data])
    sap.connect("app-removed", mock_app_removed_callback)

    sap.main_container.get_first_child()._click_on_remove_button()

    process_gtk_events()

    mock_app_removed_callback.assert_called_once()


def test_refresh_apps_are_added_to_list_when_they_are_newly_selected(mock_app_data):
    mock_app_list_refreshed_callback = Mock()

    sap = SelectedAppList(apps_to_add=[])
    sap.connect("app-list-refreshed", mock_app_list_refreshed_callback)

    sap.refresh(selected_apps=[mock_app_data])

    process_gtk_events()

    mock_app_list_refreshed_callback.assert_called_once()
    assert mock_app_list_refreshed_callback.call_args_list[0][0][1] == [mock_app_data]


def test_refresh_apps_are_removed_from_list_when_they_are_deselected(mock_app_data):
    mock_app_list_refreshed_callback = Mock()

    sap = SelectedAppList(apps_to_add=[mock_app_data])
    sap.connect("app-list-refreshed", mock_app_list_refreshed_callback)

    sap.refresh(selected_apps=[])

    process_gtk_events()

    mock_app_list_refreshed_callback.assert_called_once()
    assert mock_app_list_refreshed_callback.call_args_list[0][0][1] == []


def test_refresh_apps_list_is_not_updated_when_apps_are_untouched(mock_app_data):
    mock_app_list_refreshed_callback = Mock()

    sap = SelectedAppList(apps_to_add=[mock_app_data])
    sap.connect("app-list-refreshed", mock_app_list_refreshed_callback)

    sap.refresh(selected_apps=[mock_app_data])

    process_gtk_events()

    mock_app_list_refreshed_callback.assert_not_called()
