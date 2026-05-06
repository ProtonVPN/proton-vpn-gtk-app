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
from unittest.mock import Mock, MagicMock, PropertyMock, patch
from proton.vpn.app.gtk.widgets.headerbar.menu.settings.early_access import EarlyAccessWidget
from tests.unit.testing_utils import process_gtk_events
from proton.vpn.app.gtk import gi
from gi.repository import Gdk  # pylint: disable=C0413 # noqa: E402
from proton.vpn.connection import states
from proton.vpn.app.gtk.widgets.headerbar.menu.settings.general_settings import (
    GeneralSettings, TrayPinnedServersWidget, EntryWidget, PacketCaptureWidget
)


class TestGeneralSettings:

    def test_build_connect_at_app_startup_saves_value_when_callback_is_called(self):
        value_to_store = "new value"
        controller = Mock()
        gs = GeneralSettings(controller)
        gs.build_connect_at_app_startup()

        entry_widget = gs.get_last_child()
        entry_widget.change_value(value_to_store)

        controller.save_setting_attr.assert_called_with("app_configuration.connect_at_app_startup", value_to_store.upper())

    def test_build_connect_at_app_startup_populates_disabled_with_off(self):
        controller = Mock()
        gs = GeneralSettings(controller)
        gs.build_connect_at_app_startup()

        entry_widget = gs.get_last_child()
        entry_widget.change_value("off")

        controller.save_setting_attr.assert_called_with("app_configuration.connect_at_app_startup", None)

    @patch("proton.vpn.app.gtk.widgets.headerbar.menu.settings.general_settings.EarlyAccessWidget")
    def test_build_beta_upgrade_is_only_displayed_if_condition_allows_it(self, early_access_widget_class):
        early_access_widget = Mock()
        early_access_widget.can_early_access_be_displayed.return_value = False
        early_access_widget_class.return_value = early_access_widget

        gs = GeneralSettings(Mock())
        gs.build_beta_upgrade()

        last_child = gs.get_last_child()
        assert last_child is not early_access_widget


    @pytest.mark.parametrize("tray_indicator_mock", [None, Mock()])
    @patch("proton.vpn.app.gtk.widgets.headerbar.menu.settings.general_settings.GeneralSettings.build_start_app_minimized")
    @patch("proton.vpn.app.gtk.widgets.headerbar.menu.settings.general_settings.GeneralSettings.build_tray_pinned_servers")
    def test_display_start_app_minimized_and_tray_pinned_servers_if_tray_indicator_is_found(self, build_tray_pinned_servers_mock, build_start_app_minimized_mock, tray_indicator_mock):
        gs = GeneralSettings(MagicMock(), tray_indicator=tray_indicator_mock)
        gs.build_ui()

        if tray_indicator_mock:
            build_tray_pinned_servers_mock.assert_called_once()
            build_start_app_minimized_mock.assert_called_once()
        else:
            build_tray_pinned_servers_mock.assert_not_called()
            build_start_app_minimized_mock.assert_not_called()


class TestBuildPacketCapture:

    def _make_controller(self, protocol: str, supports_capture: bool) -> Mock:
        controller = Mock()
        controller.get_settings.return_value.protocol = protocol
        mock_cls = Mock()
        mock_cls.protocol = protocol
        mock_cls.supports_packet_capture.return_value = supports_capture
        controller.get_available_protocols.return_value = [mock_cls]
        return controller

    @pytest.mark.parametrize("supports_capture,expected_visible", [(True, True), (False, False)])
    def test_widget_visibility_matches_protocol_support(self, supports_capture, expected_visible):
        controller = self._make_controller("wireguard", supports_capture=supports_capture)
        gs = GeneralSettings(controller)
        gs.build_packet_capture()
        assert gs._packet_capture_widget.get_visible() == expected_visible

    def test_settings_changed_updates_widget_visibility(self):
        controller = self._make_controller("wireguard", supports_capture=True)
        gs = GeneralSettings(controller)
        gs.build_packet_capture()
        assert gs._packet_capture_widget.get_visible()

        non_supporting = Mock(protocol="openvpn-tcp")
        non_supporting.supports_packet_capture.return_value = False
        controller.get_available_protocols.return_value = [non_supporting]
        gs.on_settings_changed(Mock(protocol="openvpn-tcp"))
        assert not gs._packet_capture_widget.get_visible()

        supporting = Mock(protocol="wireguard")
        supporting.supports_packet_capture.return_value = True
        controller.get_available_protocols.return_value = [supporting]
        gs.on_settings_changed(Mock(protocol="wireguard"))
        assert gs._packet_capture_widget.get_visible()

class TestPacketCaptureWidget:

    def _make_widget(self, is_connected: bool = False, file_browser=lambda widget: None) -> tuple:
        controller = Mock()
        controller.is_connection_active = is_connected
        controller.get_setting_attr.return_value = "/tmp/capture.pcap"
        future = Mock()
        future.add_done_callback.side_effect = lambda cb: cb(future)
        controller.executor.submit.return_value = future
        widget = PacketCaptureWidget(controller, file_browser=file_browser)
        return widget, controller

    def test_initial_state(self):
        widget, _ = self._make_widget(is_connected=False)
        assert not widget._start_stop_button.get_sensitive()
        assert widget._start_stop_button.get_label() == "Start"
        assert not widget.capturing

        widget2, _ = self._make_widget(is_connected=True)
        assert widget2._start_stop_button.get_sensitive()

    def test_start_capture(self):
        widget, controller = self._make_widget(is_connected=True)
        widget._start_stop_button.emit("clicked")
        process_gtk_events()
        controller.executor.submit.assert_called_once_with(
            controller.current_connection.start_packet_capture
        )
        assert widget._start_stop_button.get_label() == "Stop"
        assert widget._start_stop_button.has_css_class("destructive-action")
        assert widget.capturing

    def test_stop_capture(self):
        widget, controller = self._make_widget(is_connected=True)
        widget._start_stop_button.emit("clicked")  # start
        process_gtk_events()
        controller.executor.submit.reset_mock()
        widget._start_stop_button.emit("clicked")  # stop
        process_gtk_events()
        controller.executor.submit.assert_called_once_with(
            controller.current_connection.stop_packet_capture
        )
        assert widget._start_stop_button.get_label() == "Start"
        assert not widget._start_stop_button.has_css_class("destructive-action")
        assert not widget.capturing

    def test_connection_state_changes(self):
        widget, _ = self._make_widget(is_connected=True)
        widget._start_stop_button.emit("clicked")  # start capturing
        process_gtk_events()
        assert widget.capturing

        widget._on_connection_state_changed(states.Disconnected())
        assert not widget._start_stop_button.get_sensitive()
        assert not widget.capturing
        assert widget._start_stop_button.get_label() == "Start"
        assert not widget._start_stop_button.has_css_class("destructive-action")

        widget._on_connection_state_changed(states.Connected())
        assert widget._start_stop_button.get_sensitive()

    def test_realize_unrealize(self):
        widget, controller = self._make_widget(is_connected=True)

        widget.emit("realize")
        controller.register_connection_status_subscriber.assert_called_once_with(widget)

        widget.emit("unrealize")
        controller.executor.submit.assert_not_called()
        controller.unregister_connection_status_subscriber.assert_called_once_with(widget)

        widget._start_stop_button.emit("clicked")  # start capturing
        process_gtk_events()
        assert widget.capturing
        widget.emit("unrealize")
        process_gtk_events()
        controller.executor.submit.assert_called_with(
            controller.current_connection.stop_packet_capture
        )
        assert not widget.capturing

    def test_file_browser_callable_is_used_as_browse_handler(self):
        mock_click_handler = Mock()
        mock_file_browser = Mock(return_value=mock_click_handler)
        widget, _ = self._make_widget(file_browser=mock_file_browser)
        mock_file_browser.assert_called_once_with(widget)
        assert widget._on_browse_clicked is mock_click_handler


class TestTrayPinnedServersWidget:

    def test_build_populates_entry_when_being_initialized(self):
        mock_controller = Mock(name="controller")
        mock_controller.get_setting_attr.return_value = ["PT", "CH"]
        psw = TrayPinnedServersWidget(mock_controller, Mock())

        assert psw.entry.get_text() == "PT, CH"

    def test_save_setting_when_invoking_callback(self):
        with patch.object(EntryWidget, '__init__', return_value=None) as mock_parent_init:
            tray_indicator_mock = Mock()
            controller_mock = Mock()
            gtk_entry_mock = Mock()
            raw_text = "CH, PT"
            expected_format_when_passed_to_save_setting = ["CH", "PT"]
            gtk_entry_mock.get_text.return_value = raw_text

            psw = TrayPinnedServersWidget(controller_mock, tray_indicator_mock)

            callback = mock_parent_init.call_args[1]["callback"]
            callback(gtk_entry_mock, None, None)

            controller_mock.save_setting_attr.assert_called_once_with(
                psw.SETTING_NAME, expected_format_when_passed_to_save_setting
            )
            tray_indicator_mock.reload_pinned_servers.assert_called_once()
