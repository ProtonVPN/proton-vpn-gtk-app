from unittest.mock import Mock, patch

from tests.unit.testing_utils import process_gtk_events

from proton.vpn.app.gtk.widgets.headerbar.menu.settings.split_tunneling.app.app_select_window \
    import AppSelectionWindow

from .mock_app_data import mock_app_data


def test_click_on_done_returns_selected_app_when_is_already_selected_and_app_exists_on_system(mock_app_data):
    app_selection_completed_callback = Mock()


    mock_controller = Mock(name="mock_controller")
    app_selection_window = AppSelectionWindow(
        title="Test",
        controller=mock_controller,
        stored_apps=[mock_app_data.executable],
        installed_apps=[mock_app_data]
    )
    app_selection_window.set_visible(True)
    app_selection_window.connect("app_selection_completed", app_selection_completed_callback)
    app_selection_window._click_on_done_button()

    process_gtk_events()

    app_selection_completed_callback.assert_called_once()
    assert app_selection_completed_callback.call_args_list[0][0][1] == [mock_app_data]


def test_click_on_done_returns_selected_app_when_is_not_already_selected_and_app_exists_on_system(mock_app_data):
    app_selection_completed_callback = Mock()

    mock_controller = Mock(name="mock_controller")
    app_selection_window = AppSelectionWindow(
        title="Test",
        controller=mock_controller,
        stored_apps=[],
        installed_apps=[mock_app_data]
    )
    app_selection_window.set_visible(True)
    app_selection_window.connect("app_selection_completed", app_selection_completed_callback)
    app_selection_window._get_first_app_()._set_check(True)
    app_selection_window._click_on_done_button()

    process_gtk_events()

    app_selection_completed_callback.assert_called_once()
    assert mock_app_data in app_selection_completed_callback.call_args_list[0][0][1]


def test_click_on_done_returns_no_app_when_is_already_selected_and_app_is_missing_from_system(mock_app_data):
    app_selection_completed_callback = Mock()

    mock_controller = Mock(name="mock_controller")
    app_selection_window = AppSelectionWindow(
        title="Test",
        controller=mock_controller,
        stored_apps=[mock_app_data.executable],
        installed_apps=[]
    )
    app_selection_window.set_visible(True)
    app_selection_window.connect("app_selection_completed", app_selection_completed_callback)
    app_selection_window._click_on_done_button()

    process_gtk_events()

    app_selection_completed_callback.assert_called_once()
    assert not app_selection_completed_callback.call_args_list[0][0][1]
