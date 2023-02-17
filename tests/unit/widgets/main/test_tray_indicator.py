from unittest.mock import patch, Mock

import pytest

from proton.vpn.app.gtk.widgets.main.tray_indicator import TrayIndicatorNotSupported, TrayIndicator
from tests.unit.utils import process_gtk_events


@patch("proton.vpn.app.gtk.widgets.main.tray_indicator.gi")
def test_tray_indicator_not_supported_error_is_raised_if_required_runtime_indicator_libs_are_not_available(
        patched_gi
):
    patched_gi.require_version.side_effect = ValueError("Namespace not available.")
    with pytest.raises(TrayIndicatorNotSupported):
        TrayIndicator(main_window=Mock())


@patch("proton.vpn.app.gtk.widgets.main.tray_indicator._import_app_indicator")
def test_toggle_app_visibility_menu_entry_click_shows_app_window_when_it_was_hidden(
        import_app_indicator_mock
):
    main_window = Mock()
    main_window.get_visible.return_value = False
    tray_indicator = TrayIndicator(main_window=main_window)
    tray_indicator.activate_toggle_app_visibility_menu_entry()
    process_gtk_events()
    main_window.show.assert_called_once()


@patch("proton.vpn.app.gtk.widgets.main.tray_indicator._import_app_indicator")
def test_toggle_app_visibility_menu_entry_click_hides_app_window_when_it_was_shown(
        import_app_indicator_mock
):
    main_window = Mock()
    main_window.get_visible.return_value = True
    tray_indicator = TrayIndicator(main_window=main_window)
    tray_indicator.activate_toggle_app_visibility_menu_entry()
    process_gtk_events()
    main_window.hide.assert_called_once()


@patch("proton.vpn.app.gtk.widgets.main.tray_indicator._import_app_indicator")
def test_quit_menu_entry_click_triggers_quit_header_bar_menu_entry(
        import_app_indicator_mock
):
    main_window = Mock()
    main_window.get_visible.return_value = True
    tray_indicator = TrayIndicator(main_window=main_window)
    tray_indicator.activate_quit_menu_entry()
    process_gtk_events()
    main_window.header_bar.menu.quit_button_click.assert_called_once()
