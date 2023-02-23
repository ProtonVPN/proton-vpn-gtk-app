from unittest.mock import patch, Mock

import pytest

from proton.vpn.app.gtk.widgets.main.tray_indicator import TrayIndicatorNotSupported, TrayIndicator
from tests.unit.utils import process_gtk_events
from proton.vpn.connection import states


@patch("proton.vpn.app.gtk.widgets.main.tray_indicator.gi")
def test_tray_indicator_not_supported_error_is_raised_if_required_runtime_indicator_libs_are_not_available(
        patched_gi
):
    patched_gi.require_version.side_effect = ValueError("Namespace not available.")
    with pytest.raises(TrayIndicatorNotSupported):
        TrayIndicator(controller=Mock(), main_window=Mock())


@patch("proton.vpn.app.gtk.widgets.main.tray_indicator._import_app_indicator")
def test_toggle_app_visibility_menu_entry_click_shows_app_window_when_it_was_hidden(
        import_app_indicator_mock
):
    main_window = Mock()
    main_window.get_visible.return_value = False
    tray_indicator = TrayIndicator(controller=Mock(), main_window=main_window)
    tray_indicator.activate_toggle_app_visibility_menu_entry()
    process_gtk_events()
    main_window.show.assert_called_once()


@patch("proton.vpn.app.gtk.widgets.main.tray_indicator._import_app_indicator")
def test_toggle_app_visibility_menu_entry_click_hides_app_window_when_it_was_shown(
        import_app_indicator_mock
):
    main_window = Mock()
    main_window.get_visible.return_value = True
    tray_indicator = TrayIndicator(controller=Mock(), main_window=main_window)
    tray_indicator.activate_toggle_app_visibility_menu_entry()
    process_gtk_events()
    main_window.hide.assert_called_once()


@patch("proton.vpn.app.gtk.widgets.main.tray_indicator._import_app_indicator")
def test_quit_menu_entry_click_triggers_quit_header_bar_menu_entry(
        import_app_indicator_mock
):
    main_window = Mock()
    main_window.get_visible.return_value = True
    tray_indicator = TrayIndicator(controller=Mock(), main_window=main_window)
    tray_indicator.activate_quit_menu_entry()
    process_gtk_events()
    main_window.header_bar.menu.quit_button_click.assert_called_once()


@pytest.mark.parametrize(
    "initial_state", [states.Connected, states.Disconnected, states.Error]
)
@patch("proton.vpn.app.gtk.widgets.main.tray_indicator._import_app_indicator")
def test_tray_indicator_icon_is_set_to_expected_state_icon_when_initializing_indicator(
    import_app_indicator_mock, initial_state
):
    indicator_mock = Mock()
    AppIndicator_mock = Mock()

    AppIndicator_mock.Indicator.new.return_value = indicator_mock
    import_app_indicator_mock.return_value = AppIndicator_mock

    main_window = Mock()
    main_window.get_visible.return_value = True

    controller_mock = Mock()
    controller_mock.current_connection_status = initial_state()

    tray_indicator = TrayIndicator(controller=controller_mock, main_window=main_window)
    process_gtk_events()
    indicator_mock.set_icon_full.assert_called_once_with(
        tray_indicator.icons[initial_state].file_path,
        tray_indicator.icons[initial_state].description
    )


@pytest.mark.parametrize(
    "new_state", [states.Disconnected, states.Connected, states.Error]
)
@patch("proton.vpn.app.gtk.widgets.main.tray_indicator._import_app_indicator")
def test_tray_indicator_icon_is_updated_when_vpn_connection_switches_states(
    import_app_indicator_mock, new_state
):
    indicator_mock = Mock()
    AppIndicator_mock = Mock()

    AppIndicator_mock.Indicator.new.return_value = indicator_mock
    import_app_indicator_mock.return_value = AppIndicator_mock

    main_window = Mock()
    main_window.get_visible.return_value = True

    controller_mock = Mock()
    controller_mock.current_connection_status = states.Disconnected()

    tray_indicator = TrayIndicator(controller=controller_mock, main_window=main_window)
    process_gtk_events()

    tray_indicator.status_update(new_state())
    process_gtk_events()
    indicator_mock.set_icon_full.assert_called_with(
        tray_indicator.icons[new_state].file_path,
        tray_indicator.icons[new_state].description
    )


@pytest.mark.parametrize(
    "new_state", [states.Connecting, states.Disconnecting]
)
@patch("proton.vpn.app.gtk.widgets.main.tray_indicator._import_app_indicator")
def test_tray_indicator_icon_remains_with_the_same_icon_when_status_updates_have_no_match_for_any_of_the_existing_icon_states(
   import_app_indicator_mock, new_state
):
    indicator_mock = Mock()
    AppIndicator_mock = Mock()

    AppIndicator_mock.Indicator.new.return_value = indicator_mock
    import_app_indicator_mock.return_value = AppIndicator_mock

    main_window = Mock()
    main_window.get_visible.return_value = True

    controller_mock = Mock()
    controller_mock.current_connection_status = states.Disconnected()

    tray_indicator = TrayIndicator(controller=controller_mock, main_window=main_window)
    process_gtk_events()
    
    tray_indicator.status_update(new_state())
    process_gtk_events()
    assert indicator_mock.set_icon_full.call_count == 1
