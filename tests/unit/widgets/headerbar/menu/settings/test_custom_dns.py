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
from tests.unit.testing_utils import process_gtk_events
from unittest.mock import MagicMock, Mock, patch
from proton.vpn.app.gtk.widgets.headerbar.menu.settings.custom_dns import \
    CustomDNSList, CustomDNSManager, CustomDNSWidget


class TestCustomDNSList:

    @pytest.mark.parametrize("ips_to_add", [
        [],
        ["1.1.1.1"],
        ["1.1.1.1", "2.2.2.2"],
        ["1.1.1.1", "2.2.2.2", "3.3.3.3"]
    ])
    @patch("proton.vpn.app.gtk.widgets.headerbar.menu.settings.custom_dns.CustomDNSList.pack_start")
    def test_initialize_ensure_ips_are_added_to_ui_when_a_list_with_ips_is_passed(self, pack_start_mock, ips_to_add):
        CustomDNSList(ip_list=ips_to_add)
        assert pack_start_mock.call_count == len(ips_to_add)

    @patch("proton.vpn.app.gtk.widgets.headerbar.menu.settings.custom_dns.CustomDNSList.pack_start")
    def test_successfully_add_ip_after_list_has_been_generated(self, pack_start_mock):
        new_ip = "192.159.1.1"
        existing_ips = ["1.1.1.1", "2.2.2.2", "3.3.3.3"]
        custom_dns_list = CustomDNSList(ip_list=existing_ips)
        custom_dns_list.add_ip(new_ip)

        # Since `existing_ips` is never stored internally, we need to add +1 which is the `new_ip` that we added.
        assert pack_start_mock.call_count == len(existing_ips) + 1

    @patch("proton.vpn.app.gtk.widgets.headerbar.menu.settings.custom_dns.CustomDNSList.pack_start")
    def test_successfully_delete_ip_from_list(self, pack_start_mock):
        existing_ip = "1.1.1.1"
        on_dns_ip_removed = Mock()
        custom_dns_list = CustomDNSList(ip_list=[existing_ip])

        custom_dns_list.connect("dns-ip-removed", on_dns_ip_removed)

        first_custom_dns_row = pack_start_mock.call_args[0][0]
        first_custom_dns_row.button.clicked()

        on_dns_ip_removed.assert_called_once_with(custom_dns_list, existing_ip)


class TestCustomDNSManager:

    @pytest.mark.parametrize("initial_ip_list", [
        [], ["1.1.1.1"], ["1.1.1.1", "2.2.2.2"], ["1.1.1.1", "2.2.2.2", "3.3.3.3"]
    ])
    @patch("proton.vpn.app.gtk.widgets.headerbar.menu.settings.custom_dns.get_setting")
    @patch("proton.vpn.app.gtk.widgets.headerbar.menu.settings.custom_dns.CustomDNSManager.pack_start")
    def test_ui_allows_user_to_add_new_dns_entries_after_initializing(self, pack_start_mock, get_setting_mock, initial_ip_list):
        get_setting_mock.return_value = initial_ip_list
        custom_dns_manager = CustomDNSManager(controller=Mock(), custom_dns_list=Mock())

        if len(initial_ip_list) < CustomDNSManager.DNS_LIMIT:
            assert custom_dns_manager._ui_enabled
        else:
            assert not custom_dns_manager._ui_enabled

    @pytest.mark.parametrize("initial_ip_list", [
        [], ["1.1.1.1"], ["1.1.1.1", "2.2.2.2"], ["1.1.1.1", "2.2.2.2", "3.3.3.3"]
    ])
    @patch("proton.vpn.app.gtk.widgets.headerbar.menu.settings.custom_dns.get_setting")
    @patch("proton.vpn.app.gtk.widgets.headerbar.menu.settings.custom_dns.CustomDNSManager.pack_start")
    def test_add_new_dns_ensure_ui_allows_user_to_add_new_dns_entries(self, pack_start_mock, get_setting_mock, initial_ip_list):
        get_setting_mock.return_value = initial_ip_list
        new_dns_to_be_added = "192.1.1.1"
        custom_dns_manager = CustomDNSManager(controller=Mock(), custom_dns_list=Mock())
        custom_dns_manager.set_entry_text(new_dns_to_be_added)
        custom_dns_manager.add_button_click()

        # Since the `new_dns_to_be_added` is added to initial_ip_list, it thus grows in size.
        if len(initial_ip_list) < CustomDNSManager.DNS_LIMIT:
            assert custom_dns_manager._ui_enabled
        else:
            assert not custom_dns_manager._ui_enabled

    @pytest.mark.parametrize("initial_ip_list", [
        ["1.1.1.1"], ["1.1.1.1", "2.2.2.2"], ["1.1.1.1", "2.2.2.2", "3.3.3.3"]
    ])
    @patch("proton.vpn.app.gtk.widgets.headerbar.menu.settings.custom_dns.get_setting")
    @patch("proton.vpn.app.gtk.widgets.headerbar.menu.settings.custom_dns.CustomDNSManager.pack_start")
    def test_on_delete_dns_ensure_ui_allows_user_to_add_new_dns_entries(self, pack_start_mock, get_setting_mock, initial_ip_list):
        ip_to_remove = initial_ip_list[0]
        get_setting_mock.return_value = initial_ip_list
        custom_dns_list_mock = Mock()
        custom_dns_manager = CustomDNSManager(controller=Mock(), custom_dns_list=custom_dns_list_mock)

        on_delete_callback = custom_dns_list_mock.connect.call_args[0][1]

        on_delete_callback(custom_dns_list_mock, ip_to_remove)

        assert ip_to_remove not in initial_ip_list
        assert custom_dns_manager._ui_enabled

    @patch("proton.vpn.app.gtk.widgets.headerbar.menu.settings.custom_dns.get_setting")
    @patch("proton.vpn.app.gtk.widgets.headerbar.menu.settings.custom_dns.CustomDNSManager.pack_start")
    def test_error_message_is_displayed_when_trying_to_add_invalid_dns_ip(self, pack_start_mock, get_setting_mock):
        new_dns_to_be_added = "some invalid ip"
        get_setting_mock.return_value = []
        gtk_mock = Mock()
        revealer_mock = Mock()
        add_button_mock = Mock()

        revealer_mock.get_reveal_child.return_value = False
        revealer_mock.get_children.return_value = [Mock()]

        gtk_mock.Revealer.return_value = revealer_mock
        gtk_mock.Button.return_value = add_button_mock

        custom_dns_manager = CustomDNSManager(controller=Mock(), custom_dns_list=Mock(), gtk=gtk_mock)

        on_button_clicked_callback = add_button_mock.connect.call_args[0][1]
        revealer_mock.reset_mock()

        custom_dns_manager.set_entry_text(new_dns_to_be_added)
        on_button_clicked_callback(add_button_mock, revealer_mock)

        revealer_mock.set_reveal_child.assert_called_once_with(True)

    @patch("proton.vpn.app.gtk.widgets.headerbar.menu.settings.custom_dns.save_setting")
    @patch("proton.vpn.app.gtk.widgets.headerbar.menu.settings.custom_dns.get_setting")
    @patch("proton.vpn.app.gtk.widgets.headerbar.menu.settings.custom_dns.CustomDNSManager.pack_start")
    def test_add_new_dns_ensure_it_stores_new_dns_to_file(self, pack_start_mock, get_setting_mock, save_setting):
        controller_mock = Mock(name="controller_mock")
        new_dns_to_be_added = "192.1.1.1"
        get_setting_mock.return_value = []
        custom_dns_manager = CustomDNSManager(controller=controller_mock, custom_dns_list=Mock())
        custom_dns_manager.set_entry_text(new_dns_to_be_added)
        custom_dns_manager.add_button_click()

        save_setting.assert_called_once_with(controller_mock, CustomDNSManager.SETTING_NAME, [new_dns_to_be_added])

    @patch("proton.vpn.app.gtk.widgets.headerbar.menu.settings.custom_dns.save_setting")
    @patch("proton.vpn.app.gtk.widgets.headerbar.menu.settings.custom_dns.get_setting")
    @patch("proton.vpn.app.gtk.widgets.headerbar.menu.settings.custom_dns.CustomDNSManager.pack_start")
    def test_on_delete_dns_ensure_it_removes_dns_from_file(self, pack_start_mock, get_setting_mock, save_setting):
        controller_mock = Mock(name="controller_mock")
        custom_dns_list_mock = Mock(name="custom_dns_list_mock")
        existing_dns_ip = "192.1.1.1"
        get_setting_mock.return_value = [existing_dns_ip]
        custom_dns_manager = CustomDNSManager(controller=controller_mock, custom_dns_list=custom_dns_list_mock)

        on_delete_dns_entry_callback = custom_dns_list_mock.connect.call_args[0][1]

        on_delete_dns_entry_callback(custom_dns_list_mock, existing_dns_ip)

        save_setting.assert_called_once_with(controller_mock, CustomDNSManager.SETTING_NAME, [])