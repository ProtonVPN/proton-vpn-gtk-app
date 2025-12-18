from unittest.mock import Mock

from tests.unit.testing_utils import process_gtk_events

from proton.vpn.app.gtk.widgets.headerbar.menu.settings.split_tunneling.app.data_structures \
    import AppData, AppRowWithCheckbox, AppRowWithRemoveButton

from .mock_app_data import mock_app_data


def test_app_data_coverts_from_dict_correctly(mock_app_data):
    app_dict = mock_app_data.to_dict()
    assert AppData.from_dict(app_dict) == mock_app_data


def test_build_with_remove_button_remove_signals_is_emitted_when_clicked_on_remove_button(mock_app_data):
    remove_app_callback = Mock()
    app_row = AppRowWithRemoveButton.build(mock_app_data)
    app_row.connect("remove-app", remove_app_callback)
    app_row._remove_button.emit("clicked")

    process_gtk_events()

    remove_app_callback.assert_called_once()


def test_build_with_checkbox_is_checked_when_passing_already_selected_app(mock_app_data):
    app_row = AppRowWithCheckbox.build(
        app_data=mock_app_data, checked=mock_app_data in [mock_app_data]
    )
    assert app_row.checked


def test_build_with_checkbox_is_checked_when_passing_newly_selected_app(mock_app_data):
    app_row = AppRowWithCheckbox.build(
        app_data=mock_app_data, checked=mock_app_data in []
    )
    assert not app_row.checked
