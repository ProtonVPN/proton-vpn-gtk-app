"""
Copyright (c) 2023 Proton AG

This file is part of Proton VPN.

Proton VPN is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Proton VPN is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with ProtonVPN.  If not, see <https://www.gnu.org/licenses/>.
"""
from unittest.mock import patch, Mock

import pytest

from proton.vpn.app.gtk.widgets.main.tray_indicator import TrayIndicatorNotSupported, TrayIndicator
from tests.unit.testing_utils import process_gtk_events
from proton.vpn.connection import states


@patch("proton.vpn.app.gtk.widgets.main.tray_indicator.gi")
def test_tray_indicator_not_supported_error_is_raised_if_required_runtime_indicator_libs_are_not_available(
        patched_gi
):
    patched_gi.require_version.side_effect = ValueError("Namespace not available.")
    with pytest.raises(TrayIndicatorNotSupported):
        TrayIndicator(controller=Mock(), main_window=Mock())


@pytest.fixture
def controller_mock():
    controller = Mock()
    controller.app_configuration.tray_pinned_servers = None
    return controller
    

def test_toggle_app_visibility_menu_entry_activate_shows_app_window_when_it_was_hidden(controller_mock):
    main_window = Mock()
    main_window.get_visible.return_value = False
    tray_indicator = TrayIndicator(controller=controller_mock, main_window=main_window, native_indicator=Mock())
    tray_indicator.activate_toggle_app_visibility_menu_entry()
    process_gtk_events()
    main_window.show.assert_called_once()



def test_toggle_app_visibility_menu_entry_activate_hides_app_window_when_it_was_shown(controller_mock):
    main_window = Mock()
    main_window.get_visible.return_value = True
    tray_indicator = TrayIndicator(controller=controller_mock, main_window=main_window, native_indicator=Mock())
    tray_indicator.activate_toggle_app_visibility_menu_entry()
    process_gtk_events()
    main_window.hide.assert_called_once()


def test_quit_menu_entry_activate_triggers_quit_header_bar_menu_entry(controller_mock):
    main_window = Mock()
    main_window.get_visible.return_value = True
    tray_indicator = TrayIndicator(controller=controller_mock, main_window=main_window, native_indicator=Mock())
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
    initial_state, icon, description, controller_mock
):
    """This test asserts that when the tray is initialized in any of the given states,
    the tray icon will reflect those states."""
    indicator_mock = Mock()
    main_window = Mock()
    main_window.get_visible.return_value = True

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
    new_state, icon, description, controller_mock
):
    """This test asserts that when the tray is initialized with a state, whenever a switch occurs from the
    current state to another state, the tray icon will reflect those states changes."""
    indicator_mock = Mock()
    main_window = Mock()
    main_window.get_visible.return_value = True

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
   new_state, controller_mock
):
    indicator_mock = Mock()
    main_window = Mock()
    main_window.get_visible.return_value = True

    controller_mock.current_connection_status = states.Disconnected()

    tray_indicator = TrayIndicator(controller=controller_mock, main_window=main_window, native_indicator=indicator_mock)
    process_gtk_events()
    
    tray_indicator.status_update(new_state())
    process_gtk_events()
    assert indicator_mock.set_icon_full.call_count == 1


def test_assert_connection_related_entries_are_not_displayed_when_user_is_not_logged_in(controller_mock):
    """This test asserts that when the tray is initialized and when the user is not logged in,
    none of the entries should be displayed to the user, as those require a valid session."""
    indicator_mock = Mock()
    main_window = Mock()
    main_window.get_visible.return_value = True

    controller_mock.current_connection_status = states.Disconnected()
    controller_mock.user_logged_in = False

    tray_indicator = TrayIndicator(controller=controller_mock, main_window=main_window, native_indicator=indicator_mock)
    process_gtk_events()

    assert not tray_indicator.display_connect_entry
    assert not tray_indicator.display_disconnect_entry


def test_assert_connection_related_entries_are_properly_displayed_when_user_has_logged_in(controller_mock):
    """This test asserts that when the tray is initialized, the user is logged in and there is no vpn connection.
    the connect entry is made visible to the user while the disconnect entry is hidden."""
    indicator_mock = Mock()
    main_window = Mock()
    main_window.get_visible.return_value = True

    controller_mock.user_logged_in = False
    controller_mock.current_connection_status = states.Disconnected()

    tray_indicator = TrayIndicator(controller=controller_mock, main_window=main_window, native_indicator=indicator_mock)
    process_gtk_events()

    logged_in_callback = main_window.main_widget.login_widget.connect.call_args.args[1]
    logged_in_callback()
    process_gtk_events()


    assert tray_indicator.display_connect_entry
    assert not tray_indicator.display_disconnect_entry    


@pytest.mark.parametrize(
    "initial_state, connect_entry_view_state, disconnect_entry_view_state",
    [
        (states.Disconnected(), True, False),
        (states.Disconnected(), True, False),
        (states.Connected(), False, True),
        (states.Connected(), False, True),
    ]
)
def test_assert_connection_related_entries_are_properly_displayed_when_initializing_indicator(
    initial_state,
    connect_entry_view_state, disconnect_entry_view_state,
    controller_mock
):
    """This test asserts that when the tray is initialized, the user is logged in and there is no vpn connection.
    the connect entry is made visible to the user while the disconnect entry is hidden."""
    indicator_mock = Mock()
    main_window = Mock()
    main_window.get_visible.return_value = True

    controller_mock.user_logged_in = True
    controller_mock.current_connection_status = initial_state

    tray_indicator = TrayIndicator(controller=controller_mock, main_window=main_window, native_indicator=indicator_mock)
    process_gtk_events()

    assert tray_indicator.display_connect_entry == connect_entry_view_state
    assert tray_indicator.display_disconnect_entry == disconnect_entry_view_state


def test_assert_connection_related_entries_are_hidden_when_user_has_logged_out(controller_mock):
    indicator_mock = Mock()
    main_window = Mock()
    main_window.get_visible.return_value = True

    controller_mock.user_logged_in = True
    controller_mock.current_connection_status = states.Disconnected()

    tray_indicator = TrayIndicator(controller=controller_mock, main_window=main_window, native_indicator=indicator_mock)
    process_gtk_events()

    logged_out_callback = main_window.header_bar.menu.connect.call_args.args[1]
    logged_out_callback()
    process_gtk_events()

    assert not tray_indicator.display_connect_entry
    assert not tray_indicator.display_disconnect_entry


@pytest.mark.parametrize(
    "initial_state, new_state,\
    connect_entry_final_view_state, disconnect_entry_final_view_state,\
    connect_entry_enabled, disconnect_entry_enabled",
    [
        (
            states.Disconnected(), states.Connected(),
            False, True, True, True
        ),
        (
            states.Connected(), states.Disconnected(), 
            True, False, True, True
        ),
        (
            states.Disconnected(), states.Connecting(),
            True, False, False, True
        ),
        (
            states.Connected(), states.Disconnecting(),
            False, True, True, False
        ),
    ]
)
def test_assert_connection_related_entries_are_properly_displayed_when_vpn_connection_switches_states(
    initial_state, new_state,
    connect_entry_final_view_state, disconnect_entry_final_view_state,
    connect_entry_enabled, disconnect_entry_enabled,
    controller_mock
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

    controller_mock.user_logged_in = True
    controller_mock.current_connection_status = initial_state

    tray_indicator = TrayIndicator(controller=controller_mock, main_window=main_window, native_indicator=indicator_mock)
    process_gtk_events()

    tray_indicator.status_update(new_state)
    process_gtk_events()

    assert tray_indicator.display_connect_entry == connect_entry_final_view_state
    assert tray_indicator.display_disconnect_entry == disconnect_entry_final_view_state
    assert tray_indicator.enable_connect_entry == connect_entry_enabled
    assert tray_indicator.enable_disconnect_entry == disconnect_entry_enabled


def test_connect_entry_connects_to_vpn_when_activated(controller_mock):
    indicator_mock = Mock()
    main_window = Mock()
    main_window.get_visible.return_value = True

    controller_mock.user_logged_in = True
    controller_mock.current_connection_status = states.Disconnected()

    tray_indicator = TrayIndicator(controller=controller_mock, main_window=main_window, native_indicator=indicator_mock)
    process_gtk_events()

    tray_indicator.active_connect_entry()
    controller_mock.connect_to_fastest_server.assert_called_once()


def test_connect_pinned_server_entry_connects_to_vpn_when_activated(controller_mock):
    indicator_mock = Mock()
    main_window = Mock()
    main_window.get_visible.return_value = True

    pinned_server = "TEST#30"
    controller_mock.user_logged_in = True
    controller_mock.current_connection_status = states.Disconnected()
    controller_mock.app_configuration.tray_pinned_servers = [pinned_server]

    tray_indicator = TrayIndicator(controller=controller_mock, main_window=main_window, native_indicator=indicator_mock)
    process_gtk_events()

    tray_indicator.activate_top_most_pinned_server_entry()
    controller_mock.connect_to_server.assert_called_once_with(pinned_server)


def test_disconnect_entry_disconnects_from_vpn_when_user_is_connected(controller_mock):
    indicator_mock = Mock()
    main_window = Mock()
    main_window.get_visible.return_value = True

    controller_mock.user_logged_in = True
    controller_mock.current_connection_status = states.Connected()

    tray_indicator = TrayIndicator(controller=controller_mock, main_window=main_window, native_indicator=indicator_mock)
    process_gtk_events()

    tray_indicator.activate_disconnect_entry()
    controller_mock.disconnect.assert_called_once()
