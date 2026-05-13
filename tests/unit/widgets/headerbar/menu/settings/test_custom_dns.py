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
import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk

from proton.vpn.core.settings import CustomDNSEntry
from tests.unit.testing_utils import process_gtk_events
from unittest.mock import MagicMock, Mock, patch
from proton.vpn.app.gtk.widgets.headerbar.menu.settings.custom_dns import \
    CustomDNSList, CustomDNSManager, CustomDNSWidget
from proton.vpn.core.settings import NetShield

FREE_TIER = 0
PLUS_TIER = 1


def widget_child_count(widget: Gtk.Widget) -> int:
    child = widget.get_first_child()
    child_count = 0
    while child is not None:
        child_count += 1
        child = child.get_next_sibling()

    return child_count


class TestCustomDNSList:

    @pytest.mark.parametrize("ips_to_add", [
        [],
        [CustomDNSEntry.new_from_string("1.1.1.1")],
        [CustomDNSEntry.new_from_string("1.1.1.1"), CustomDNSEntry.new_from_string("2.2.2.2")],
        [CustomDNSEntry.new_from_string("1.1.1.1"), CustomDNSEntry.new_from_string("2.2.2.2"), CustomDNSEntry.new_from_string("3.3.3.3")]
    ])
    def test_initialize_ensure_ips_are_added_to_ui_when_a_list_with_ips_is_passed(self, ips_to_add):
        custom_dns_list = CustomDNSList(ip_list=ips_to_add)
        ip_count = widget_child_count(custom_dns_list)
        assert ip_count == len(ips_to_add)

    def test_successfully_add_ip_after_list_has_been_generated(self):
        new_ip = "192.159.1.1"
        existing_ips = [CustomDNSEntry.new_from_string("1.1.1.1"),
                        CustomDNSEntry.new_from_string("2.2.2.2"),
                        CustomDNSEntry.new_from_string("3.3.3.3")]
        custom_dns_list = CustomDNSList(ip_list=existing_ips)
        custom_dns_list.add_dns(CustomDNSEntry.new_from_string(new_ip))
        ip_count = widget_child_count(custom_dns_list)

        # Since `existing_ips` is never stored internally, we need to add +1 which is the `new_ip` that we added.
        assert ip_count == len(existing_ips) + 1

    def test_successfully_delete_ip_from_list(self):
        existing_ip = CustomDNSEntry.new_from_string("1.1.1.1")
        on_dns_ip_removed = Mock()
        custom_dns_list = CustomDNSList(ip_list=[existing_ip])

        custom_dns_list.connect("dns-ip-removed", on_dns_ip_removed)

        first_custom_dns_row = custom_dns_list.get_first_child()
        first_custom_dns_row.button.emit("clicked")

        on_dns_ip_removed.assert_called_once_with(custom_dns_list, existing_ip)


class TestCustomDNSManager:

    @patch("proton.vpn.app.gtk.widgets.headerbar.menu.settings.custom_dns.CustomDNSManager.append")
    def test_error_message_is_displayed_when_trying_to_add_invalid_dns_ip(self, _):
        mock_controller = Mock(name="controller")
        mock_controller.get_setting_attr.return_value = []
        new_dns_to_be_added = "some invalid ip"
        gtk_mock = Mock()
        revealer_mock = Mock()
        add_button_mock = Mock()

        revealer_mock.get_reveal_child.return_value = False
        revealer_mock.get_children.return_value = [Mock()]

        gtk_mock.Revealer.return_value = revealer_mock
        gtk_mock.Button.return_value = add_button_mock

        custom_dns_manager = CustomDNSManager(controller=mock_controller,
                                              custom_dns_list=Mock(),
                                              gtk=gtk_mock)

        on_button_clicked_callback = add_button_mock.connect.call_args[0][1]
        revealer_mock.reset_mock()

        custom_dns_manager.set_entry_text(new_dns_to_be_added)
        on_button_clicked_callback(add_button_mock)

        revealer_mock.set_reveal_child.assert_called_once_with(True)

    @patch("proton.vpn.app.gtk.widgets.headerbar.menu.settings.custom_dns.CustomDNSManager.append")
    def test_add_new_dns_ensure_it_stores_new_dns_to_file(self, _):
        controller_mock = Mock(name="controller_mock")
        controller_mock.get_setting_attr.return_value = []
        new_dns_to_be_added = CustomDNSEntry.new_from_string("192.1.1.1")
        custom_dns_manager = CustomDNSManager(controller=controller_mock, custom_dns_list=Mock())
        custom_dns_manager.set_entry_text(str(new_dns_to_be_added.ip))
        custom_dns_manager.add_button_click()

        controller_mock.save_setting_attr.assert_called_once_with(CustomDNSManager.SETTING_NAME, [new_dns_to_be_added])

    @patch("proton.vpn.app.gtk.widgets.headerbar.menu.settings.custom_dns.CustomDNSManager.append")
    def test_on_delete_dns_ensure_it_removes_dns_from_file(self, pack_start_mock):
        existing_dns_ip = CustomDNSEntry.new_from_string("192.1.1.1")
        controller_mock = Mock(name="controller_mock")
        controller_mock.get_setting_attr.return_value = [existing_dns_ip]

        custom_dns_list_mock = Mock(name="custom_dns_list_mock")
        custom_dns_manager = CustomDNSManager(controller=controller_mock, custom_dns_list=custom_dns_list_mock)

        on_delete_dns_entry_callback = custom_dns_list_mock.connect.call_args[0][1]

        on_delete_dns_entry_callback(custom_dns_list_mock, existing_dns_ip)

        controller_mock.save_setting_attr.assert_called_once_with(CustomDNSManager.SETTING_NAME, [])


class TestCustomDNSWidget:

    @pytest.mark.parametrize("response_type", [-8, -9])
    @patch("proton.vpn.app.gtk.widgets.headerbar.menu.settings.custom_dns.ConfirmationDialog")
    @patch("proton.vpn.app.gtk.widgets.headerbar.menu.settings.custom_dns.CustomDNSWidget.off")
    def test_disable_custom_dns_and_prompt_user_via_dialog_when_enabling_netshield_while_custom_dns_is_enabled_and_ensure_that_either_custom_dns_or_netshield_is_disabled(self, custom_dns_off_mock, confirmation_dialog_mock, response_type):
        controller_mock = Mock(name="controller_mock")
        controller_mock.get_setting_attr.return_value = True
        controller_mock.user_tier = PLUS_TIER
        settings_window_mock = Mock(name="settings_window_mock")
        feature_settings_mock = Mock(name="feature_settings_mock")
        gtk_mock = Mock(name="gtk_mock")
        confirmation_dialog_instance_mock = Mock(name="confirmation_dialog_instance_mock")
        confirmation_dialog_mock.return_value = confirmation_dialog_instance_mock

        dns_widget = CustomDNSWidget(controller=controller_mock, settings_window=settings_window_mock, gtk=gtk_mock)

        dns_widget.on_netshield_setting_changed(feature_settings_mock, new_setting=NetShield.BLOCK_MALICIOUS_URL)

        on_dialog_button_click_callback = confirmation_dialog_instance_mock.connect.call_args[0][1]

        on_dialog_button_click_callback(confirmation_dialog_instance_mock, response_type)

        # -8: Gtk.ResponseType.YES
        # -9: Gtk.ResponseType.NO
        Gtk_ResponseType_YES = -8

        if response_type == Gtk_ResponseType_YES:
            custom_dns_off_mock.assert_called_once()
            feature_settings_mock.netshield.off.assert_not_called()
        else:
            feature_settings_mock.netshield.off.assert_called_once()
            custom_dns_off_mock.assert_not_called()

    @patch("proton.vpn.app.gtk.widgets.headerbar.menu.settings.custom_dns.ConfirmationDialog")
    def test_custom_dns_prompt_is_not_shown_to_the_user_when_custom_dns_is_disabled_while_enabling_netshield(self, confirmation_dialog_mock):
        controller_mock = Mock(name="controller_mock")
        controller_mock.get_setting_attr.return_value = False
        controller_mock.user_tier = PLUS_TIER
        settings_window_mock = Mock(name="settings_window_mock")
        feature_settings_mock = Mock(name="feature_settings_mock")
        confirmation_dialog_instance_mock = Mock(name="confirmation_dialog_instance_mock")
        confirmation_dialog_mock.return_value = confirmation_dialog_instance_mock

        dns_widget = CustomDNSWidget(controller=controller_mock, settings_window=settings_window_mock)

        dns_widget.on_netshield_setting_changed(feature_settings_mock, new_setting=NetShield.NO_BLOCK)

        confirmation_dialog_mock.assert_not_called()
