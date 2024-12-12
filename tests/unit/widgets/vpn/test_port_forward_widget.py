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
import pytest
from unittest.mock import Mock, patch, PropertyMock
from proton.vpn.app.gtk.widgets.vpn.port_forward_widget import PortForwardRevealer, PortForwardWidget
from proton.vpn.connection import states


class TestPortForwardRevealer:

    @pytest.mark.parametrize("new_reveal_value", [True, False])
    @patch("proton.vpn.app.gtk.widgets.vpn.port_forward_widget.PortForwardRevealer.add")
    @patch("proton.vpn.app.gtk.widgets.vpn.port_forward_widget.PortForwardRevealer.set_reveal_child")
    def test_revealer_updates_child_reveal_state_when_passing_new_value(self, set_reveal_child_mock, _, new_reveal_value):
        port_forward_widget_mock = Mock(name="PortForwardWidget")
        PortForwardRevealer(
            port_forward_widget=port_forward_widget_mock
        )
        on_update_port_forwarding_visibility_callback = port_forward_widget_mock.connect.call_args[0][1]
        on_update_port_forwarding_visibility_callback(port_forward_widget_mock, new_reveal_value)

        set_reveal_child_mock.assert_called_once_with(new_reveal_value)

    @patch("proton.vpn.app.gtk.widgets.vpn.port_forward_widget.PortForwardRevealer.add")
    def test_revealer_proxies_state_when_receiving_new_state_to_child(self, _):
        connected_state = states.Connected()
        port_forward_widget_mock = Mock(name="PortForwardWidget")
        pfrevealer = PortForwardRevealer(
            port_forward_widget=port_forward_widget_mock
        )

        pfrevealer.on_new_state(connected_state)

        port_forward_widget_mock.on_new_state.assert_called_once_with(connected_state)


class TestPortForwardWidget:
    @pytest.mark.parametrize("new_state,port_value,is_widget_visible", [
        (states.Connected(), None, False),
        (states.Connected(), 443, True),
        (states.Connecting(), None, False),
        (states.Connecting(), 443, False),
        (states.Disconnected(), 443, False),
        (states.Disconnected(), 443, False),
        (states.Disconnecting(), 443, False),
        (states.Disconnecting(), 443, False),
        (states.Error(), 443, False),
        (states.Error(), 443, False),
    ])
    @patch("proton.vpn.app.gtk.widgets.vpn.port_forward_widget.states.State.forwarded_port", new_callable=PropertyMock)
    @patch("proton.vpn.app.gtk.widgets.vpn.port_forward_widget.PortForwardWidget.emit")
    def test_on_new_state_widget_visibility_is_updated_accordingly_when_a_new_state_is_received(
        self, emit_mock, forwarded_port_mock, new_state, port_value, is_widget_visible
    ):
        clipboard_mock = Mock(name="clipboard")
        pfwidget = PortForwardWidget(clipboard=clipboard_mock)
        forwarded_port_mock.return_value = port_value
        pfwidget.on_new_state(new_state)

        emit_mock.assert_called_once_with("update-visibility", is_widget_visible)

    @patch("proton.vpn.app.gtk.widgets.vpn.port_forward_widget.PortForwardWidget.connect")
    def test_on_button_press_ensure_port_is_copied_to_clipboard(self, connect_mock):
        port = 443
        number_of_bytes_in_the_string = len(str(port).encode("utf-8"))
        clipboard_mock = Mock(name="clipboard")
        pfwidget = PortForwardWidget(clipboard=clipboard_mock)
        pfwidget.set_port_forward_label(port)

        on_button_press_callback = connect_mock.call_args_list[0][0][1]
        on_button_press_callback(pfwidget, Mock(name="Gdk.EventButton"))

        clipboard_mock.set_text.assert_called_once_with(str(port), number_of_bytes_in_the_string)
