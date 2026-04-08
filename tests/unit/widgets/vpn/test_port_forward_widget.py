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
from proton.vpn.connection import states, events
from gi.repository import Gtk, GObject  # pylint: disable=C0413 # noqa: E402


def _make_state(active_port):
    return states.Connected(states.StateContext(
        event=events.Connected(events.EventContext(
            connection=Mock(),
            forwarded_port=active_port
        ))
    ))


class TestPortForwardRevealer:

    @pytest.mark.parametrize("new_reveal_value", [True, False])
    def test_revealer_updates_child_reveal_state_when_passing_new_value(self, new_reveal_value):
        port_forward_widget = PortForwardWidget(Mock())
        revealer = PortForwardRevealer(
            port_forward_widget=port_forward_widget, notifications=Mock()
        )

        port_forward_widget.emit("update-visibility", new_reveal_value)
        assert revealer.get_reveal_child() == new_reveal_value
        

    @patch("proton.vpn.app.gtk.widgets.vpn.port_forward_widget.PortForwardRevealer.set_child")
    def test_revealer_proxies_state_when_receiving_new_state_to_child(self, _):
        connected_state = states.Connected()
        port_forward_widget_mock = Mock(name="PortForwardWidget")
        pfrevealer = PortForwardRevealer(
            port_forward_widget=port_forward_widget_mock, notifications=Mock()
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
        pfwidget = PortForwardWidget(notifications=Mock(), clipboard=Mock())
        forwarded_port_mock.return_value = port_value
        pfwidget.on_new_state(new_state)

        emit_mock.assert_called_once_with("update-visibility", is_widget_visible)

    def test_on_new_state_shows_port_forwarding_notification_if_port_changed(self):
        notifications_mock = Mock()
        pfwidget = PortForwardWidget(
            notifications=notifications_mock,
            clipboard=Mock(),
            forwarded_port=None
        )

        # Patch get_toplevel to return a hidden window
        # so that the notification is shown.
        pfwidget._port_forward_label.get_root = Mock(
            return_value=Mock(is_active=Mock(return_value=False), spec=Gtk.Window)
        )

        # We expect a notification the first time.
        active_port = 1234
        pfwidget.on_new_state(_make_state(active_port=active_port))

        notifications_mock.show_gnome_notification.assert_called_once_with(
            title="Port forwarding",
            description=f"Active port is {active_port}"
        )

        # And we expect a notification when the port changes.
        pfwidget.on_new_state(_make_state(active_port=5678))

        notifications_mock.show_gnome_notification.assert_called()

    def test_on_new_state_does_not_show_port_forwarding_notification_if_port_did_not_change(self):
        notifications_mock = Mock()

        pfwidget = PortForwardWidget(
            notifications=notifications_mock,
            clipboard=Mock(),
            forwarded_port=None
        )

        # Patch get_toplevel to return a hidden window
        # so that the notification is shown if it should be.
        pfwidget._port_forward_label.get_root = Mock(
            return_value=Mock(is_active=Mock(return_value=False), spec=Gtk.Window)
        )

        # Two state changes with the same port should not trigger a
        # notification.
        pfwidget.on_new_state(_make_state(active_port=1234))
        pfwidget.on_new_state(_make_state(active_port=1234))

        notifications_mock.show_gnome_notification.assert_called_once()

    def test_on_new_state_does_not_show_port_forwarding_notification_if_new_state_has_no_port(self):
        notifications_mock = Mock()
        pfwidget = PortForwardWidget(notifications=notifications_mock, clipboard=Mock(), forwarded_port=1234)
        new_state = states.Connected(states.StateContext(
            event=events.Connected(events.EventContext(
                connection=Mock(),
                forwarded_port=None
            ))
        ))

        pfwidget.on_new_state(new_state)

        notifications_mock.show_gnome_notification.assert_not_called()

    def test_on_button_press_ensure_port_is_copied_to_clipboard(self):
        port = 443
        clipboard_mock = Mock()
        pfwidget = PortForwardWidget(notifications=Mock(), clipboard=clipboard_mock)
        pfwidget.set_port_forward_label(port)

        pfwidget.click_copy_button()
        value: GObject.Value = clipboard_mock.set.call_args_list[0][0][0]
        assert value.get_string() == str(port)
