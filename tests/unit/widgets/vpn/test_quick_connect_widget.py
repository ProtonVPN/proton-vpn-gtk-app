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
from unittest.mock import Mock

import pytest
from gi.repository import GLib

from proton.vpn.app.gtk import Gtk
from proton.vpn.app.gtk.controller import Controller
from proton.vpn.app.gtk.widgets.vpn.quick_connect_widget import QuickConnectWidget
from proton.vpn.connection.states import Disconnected, Connected, Connecting, Error
from tests.unit.testing_utils import process_gtk_events, run_main_loop


@pytest.mark.parametrize("connection_state, connect_button_visible, disconnect_button_visible, disconnect_button_label", [
    (Disconnected(), True, False, None),
    (Connecting(), False, True, "Cancel Connection"),
    (Connected(), False, True, "Disconnect"),
    (Error(), False, True, "Cancel Reconnection")
])
def test_quick_connect_widget_changes_button_according_to_connection_state_changes(
        connection_state, connect_button_visible, disconnect_button_visible, disconnect_button_label
):
    quick_connect_widget = QuickConnectWidget(controller=Mock())
    window = Gtk.Window()
    window.add(quick_connect_widget)
    main_loop = GLib.MainLoop()

    def run():
        window.show_all()

        quick_connect_widget.connection_status_update(connection_state)

        try:
            assert quick_connect_widget.connection_state is connection_state
            assert quick_connect_widget.connect_button.get_visible() is connect_button_visible
            assert quick_connect_widget.disconnect_button.get_visible() is disconnect_button_visible
            if disconnect_button_label:
                assert quick_connect_widget.disconnect_button.get_label() == disconnect_button_label
        finally:
            main_loop.quit()

    GLib.idle_add(run)
    run_main_loop(main_loop)


def test_quick_connect_widget_connects_to_fastest_server_when_connect_button_is_clicked():
    api_mock = Mock()
    controller = Controller(thread_pool_executor=Mock(), api=api_mock)
    quick_connect_widget = QuickConnectWidget(controller=controller)

    quick_connect_widget.connect_button.clicked()
    process_gtk_events()

    api_mock.servers.get_fastest_server.assert_called_once()
    api_mock.connection.connect.assert_called_once()


def test_quick_connect_widget_disconnects_from_current_server_when_disconnect_is_clicked():
    api_mock = Mock()
    controller = Controller(thread_pool_executor=Mock(), api=api_mock)
    quick_connect_widget = QuickConnectWidget(controller=controller)

    quick_connect_widget.disconnect_button.clicked()
    process_gtk_events()

    api_mock.connection.disconnect.assert_called_once()
