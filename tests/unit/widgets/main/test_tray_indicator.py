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


def test_toggle_app_visibility_menu_entry_click_shows_app_window_when_it_was_hidden():
    main_window = Mock()
    main_window.get_visible.return_value = False
    tray_indicator = TrayIndicator(controller=Mock(), main_window=main_window, native_indicator=Mock())
    tray_indicator.activate_toggle_app_visibility_menu_entry()
    process_gtk_events()
    main_window.show.assert_called_once()



def test_toggle_app_visibility_menu_entry_click_hides_app_window_when_it_was_shown():
    main_window = Mock()
    main_window.get_visible.return_value = True
    tray_indicator = TrayIndicator(controller=Mock(), main_window=main_window, native_indicator=Mock())
    tray_indicator.activate_toggle_app_visibility_menu_entry()
    process_gtk_events()
    main_window.hide.assert_called_once()


def test_quit_menu_entry_click_triggers_quit_header_bar_menu_entry():
    main_window = Mock()
    main_window.get_visible.return_value = True
    tray_indicator = TrayIndicator(controller=Mock(), main_window=main_window, native_indicator=Mock())
    tray_indicator.activate_quit_menu_entry()
    process_gtk_events()
    main_window.header_bar.menu.quit_button_click.assert_called_once()


@pytest.mark.parametrize(
    "initial_state, icon, description", [
        (states.Connected(), TrayIndicator.CONNECTED_ICON, TrayIndicator.CONNECTED_ICON_DESCRIPTION),
        (states.Disconnected(), TrayIndicator.DISCONNECTED_ICON, TrayIndicator.DISCONNECTED_ICON_DESCRIPTION),
        (states.Error(), TrayIndicator.ERROR_ICON, TrayIndicator.ERROR_ICON_DESCRIPTION)
    ]
)
def test_tray_indicator_icon_is_set_to_expected_state_icon_when_initializing_indicator(
    initial_state, icon, description
):
    """This test asserts that when the tray is initialized in any of the given states,
    the tray icon will reflect those states."""
    indicator_mock = Mock()
    main_window = Mock()
    main_window.get_visible.return_value = True

    controller_mock = Mock()
    controller_mock.current_connection_status = initial_state

    tray_indicator = TrayIndicator(controller=controller_mock, main_window=main_window, native_indicator=indicator_mock)
    process_gtk_events()
    indicator_mock.set_icon_full.assert_called_once_with(icon, description)


@pytest.mark.parametrize(
    "new_state, icon, description", [
        (states.Connected(), TrayIndicator.CONNECTED_ICON, TrayIndicator.CONNECTED_ICON_DESCRIPTION),
        (states.Disconnected(), TrayIndicator.DISCONNECTED_ICON, TrayIndicator.DISCONNECTED_ICON_DESCRIPTION),
        (states.Error(), TrayIndicator.ERROR_ICON, TrayIndicator.ERROR_ICON_DESCRIPTION)
    ]
)
def test_tray_indicator_icon_is_updated_when_vpn_connection_switches_states(
    new_state, icon, description
):
    """This test asserts that when the tray is initialized with a state, whenever a switch occurs from the
    current state to another state, the tray icon will reflect those states changes."""
    indicator_mock = Mock()
    main_window = Mock()
    main_window.get_visible.return_value = True

    controller_mock = Mock()
    controller_mock.current_connection_status = states.Disconnected()

    tray_indicator = TrayIndicator(controller=controller_mock, main_window=main_window, native_indicator=indicator_mock)
    process_gtk_events()

    tray_indicator.status_update(new_state)
    process_gtk_events()
    indicator_mock.set_icon_full.assert_called_with(icon, description)


@pytest.mark.parametrize(
    "new_state", [states.Connecting, states.Disconnecting]
)
def test_tray_indicator_icon_remains_with_the_same_icon_when_status_updates_have_no_match_for_any_of_the_existing_icon_states(
   new_state
):
    indicator_mock = Mock()
    main_window = Mock()
    main_window.get_visible.return_value = True

    controller_mock = Mock()
    controller_mock.current_connection_status = states.Disconnected()

    tray_indicator = TrayIndicator(controller=controller_mock, main_window=main_window, native_indicator=indicator_mock)
    process_gtk_events()
    
    tray_indicator.status_update(new_state())
    process_gtk_events()
    assert indicator_mock.set_icon_full.call_count == 1


def test_assert_connection_related_entries_are_not_displayed_when_user_is_not_logged_in():
    """This test asserts that when the tray is initialized and when the user is not logged in,
    none of the entries should be displayed to the user, as those require a valid session."""
    indicator_mock = Mock()
    main_window = Mock()
    main_window.get_visible.return_value = True

    controller_mock = Mock()
    controller_mock.current_connection_status = states.Disconnected()
    controller_mock.user_logged_in = False

    tray_indicator = TrayIndicator(controller=controller_mock, main_window=main_window, native_indicator=indicator_mock)
    process_gtk_events()

    assert not tray_indicator.is_connect_button_displayed
    assert not tray_indicator.is_disconnect_button_displayed


def test_assert_connection_related_entries_are_properly_displayed_when_user_has_logged_in():
    """This test asserts that when the tray is initialized, the user is logged in and there is no vpn connection.
    the connect entry is made visible to the user while the disconnect entry is hidden."""
    indicator_mock = Mock()
    main_window = Mock()
    main_window.get_visible.return_value = True

    controller_mock = Mock()
    controller_mock.user_logged_in = False
    controller_mock.current_connection_status = states.Disconnected()

    tray_indicator = TrayIndicator(controller=controller_mock, main_window=main_window, native_indicator=indicator_mock)
    process_gtk_events()

    logged_in_callback = main_window.main_widget.login_widget.connect.call_args.args[1]
    logged_in_callback()
    process_gtk_events()


    assert tray_indicator.is_connect_button_displayed
    assert not tray_indicator.is_disconnect_button_displayed    


@pytest.mark.parametrize(
    "initial_state, connect_button_view_state, disconnect_button_view_state",
    [
        (states.Disconnected(), True, False),
        (states.Connected(), False, True),
    ]
)
def test_assert_connection_related_entries_are_properly_displayed_when_initializing_indicator(
    initial_state, connect_button_view_state, disconnect_button_view_state
):
    """This test asserts that when the tray is initialized, the user is logged in and there is no vpn connection.
    the connect entry is made visible to the user while the disconnect entry is hidden."""
    indicator_mock = Mock()
    main_window = Mock()
    main_window.get_visible.return_value = True

    controller_mock = Mock()
    controller_mock.user_logged_in = True
    controller_mock.current_connection_status = initial_state

    tray_indicator = TrayIndicator(controller=controller_mock, main_window=main_window, native_indicator=indicator_mock)
    process_gtk_events()

    assert tray_indicator.is_connect_button_displayed == connect_button_view_state
    assert tray_indicator.is_disconnect_button_displayed == disconnect_button_view_state


def test_assert_connection_related_entries_are_hidden_when_user_has_logged_out():
    indicator_mock = Mock()
    main_window = Mock()
    main_window.get_visible.return_value = True

    controller_mock = Mock()
    controller_mock.user_logged_in = True
    controller_mock.current_connection_status = states.Disconnected()

    tray_indicator = TrayIndicator(controller=controller_mock, main_window=main_window, native_indicator=indicator_mock)
    process_gtk_events()

    logged_out_callback = main_window.header_bar.menu.connect.call_args.args[1]
    logged_out_callback()
    process_gtk_events()

    assert not tray_indicator.is_connect_button_displayed
    assert not tray_indicator.is_disconnect_button_displayed


@pytest.mark.parametrize(
    "initial_state, new_state,\
    connect_button_final_view_state, disconnect_button_final_view_state,\
    connect_button_enabled, disconnect_button_enabled",
    [
        (states.Disconnected(), states.Connected(), False, True, True, True),
        (states.Connected(), states.Disconnected(), True, False, True, True),
        (states.Disconnected(), states.Connecting(), True, False, False, True),
        (states.Connected(), states.Disconnecting(), False, True, True, False),
    ]
)
def test_assert_connection_related_entries_are_properly_displayed_when_vpn_connection_switches_states(
    initial_state, new_state,
    connect_button_final_view_state, disconnect_button_final_view_state,
    connect_button_enabled, disconnect_button_enabled
):
    """This test asserts that when switching states, that the connect entry is displayed when the connection status
    switches to disconnected/disconnecting state, and that the disconnect entry is displayed when the connection status
    switches to connected/connecting state.
    
    This test also respectively asserts that the connect entry is not-clickable when the connection switches to connecting
    state, and that the disconnect entry is not-clickable when the connection switchets to disconnectin state. 
    """
    indicator_mock = Mock()
    main_window = Mock()
    main_window.get_visible.return_value = True

    controller_mock = Mock()
    controller_mock.user_logged_in = True
    controller_mock.current_connection_status = initial_state

    tray_indicator = TrayIndicator(controller=controller_mock, main_window=main_window, native_indicator=indicator_mock)
    process_gtk_events()

    tray_indicator.status_update(new_state)
    process_gtk_events()

    assert tray_indicator.is_connect_button_displayed == connect_button_final_view_state
    assert tray_indicator.is_disconnect_button_displayed == disconnect_button_final_view_state
    assert tray_indicator.enable_connect_entry == connect_button_enabled
    assert tray_indicator.enable_disconnect_entry == disconnect_button_enabled


def test_connect_entry_connects_to_vpn_when_clicked():
    indicator_mock = Mock()
    main_window = Mock()
    main_window.get_visible.return_value = True

    controller_mock = Mock()
    controller_mock.user_logged_in = True
    controller_mock.current_connection_status = states.Disconnected()

    tray_indicator = TrayIndicator(controller=controller_mock, main_window=main_window, native_indicator=indicator_mock)
    process_gtk_events()

    tray_indicator.connect_button_click()
    controller_mock.connect_to_fastest_server.assert_called_once()


def test_disconnect_entry_disconnects_from_vpn_when_user_is_connected():
    indicator_mock = Mock()
    main_window = Mock()
    main_window.get_visible.return_value = True

    controller_mock = Mock()
    controller_mock.user_logged_in = True
    controller_mock.current_connection_status = states.Connected()

    tray_indicator = TrayIndicator(controller=controller_mock, main_window=main_window, native_indicator=indicator_mock)
    process_gtk_events()

    tray_indicator.disconnect_button_click()
    controller_mock.disconnect.assert_called_once()
