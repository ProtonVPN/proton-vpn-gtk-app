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

from unittest.mock import Mock, patch
from proton.vpn.app.gtk.widgets.headerbar.menu.settings.connection_settings import (
    ConnectionSettings, ProtocolComboboxWidget
)
from proton.vpn.app.gtk.controller import Controller

FREE_TIER = 0
PLUS_TIER = 1


def test_build_vpn_accelerator_save_new_value_when_callback_is_called():
    controller_mock = Mock(spec=Controller)
    controller_mock.user_tier = PLUS_TIER
    settings_window_mock = Mock()
    cs = ConnectionSettings(controller_mock, settings_window_mock)
    cs.build_vpn_accelerator()
    new_value = False

    toggle_widget = cs.get_last_child()
    toggle_widget.switch.set_active(new_value)

    controller_mock.save_setting_attr.assert_called_once_with("settings.features.vpn_accelerator", new_value)
    settings_window_mock.notify_user_with_reconnect_message.assert_not_called()


def test_build_moderate_nat_save_new_value_when_callback_is_called():
    controller_mock = Mock()
    controller_mock.user_tier = PLUS_TIER
    settings_window_mock = Mock()
    cs = ConnectionSettings(controller_mock, settings_window_mock)
    cs.build_moderate_nat()
    new_value = False

    toggle_widget = cs.get_last_child()
    toggle_widget.switch.set_active(new_value)

    controller_mock.save_setting_attr.assert_called_once_with("settings.features.moderate_nat", new_value)
    settings_window_mock.notify_user_with_reconnect_message.assert_not_called()


def test_build_ipv6_save_new_value_when_callback_is_called():
    controller_mock = Mock()
    controller_mock.user_tier = PLUS_TIER
    settings_window_mock = Mock()
    cs = ConnectionSettings(controller_mock, settings_window_mock)
    cs.build_ipv6()
    new_value = False

    toggle_widget = cs.get_last_child()
    toggle_widget.switch.set_active(new_value)

    controller_mock.save_setting_attr.assert_called_once_with("settings.ipv6", new_value)
    settings_window_mock.notify_user_with_reconnect_message.assert_called_once()


def _make_mock_protocol(protocol_id, ui_protocol):
    p = Mock()
    p.protocol = protocol_id
    p.ui_protocol = ui_protocol
    return p


_GENERIC_PROTOCOLS = [
    _make_mock_protocol("openvpn-tcp", "OpenVPN (TCP)"),
    _make_mock_protocol("wireguard", "WireGuard"),
]
_PROTUN_PROTOCOLS = [
    _make_mock_protocol("protun-tcp", "ProTun (TCP)"),
]


def _make_controller(current_protocol="wireguard", protun_protocols=None, generic_protocols=None):
    if protun_protocols is None:
        protun_protocols = _PROTUN_PROTOCOLS
    if generic_protocols is None:
        generic_protocols = _GENERIC_PROTOCOLS
    controller = Mock()
    controller.get_setting_attr.return_value = current_protocol
    controller.connection_disconnected = True
    controller.user_tier = PLUS_TIER
    controller.setting_attr_has_conflict.return_value = None

    def get_available_protocols(group):
        if group == ProtocolComboboxWidget.PROTUN_PROTOCOL_GROUP:
            return list(protun_protocols)
        return list(generic_protocols)

    controller.get_available_protocols.side_effect = get_available_protocols
    return controller


def _make_protocol_widget(controller=None, current_protocol="wireguard"):
    if controller is None:
        controller = _make_controller(current_protocol)
    return ProtocolComboboxWidget(
        controller=controller,
        title="Protocol",
        description="...",
        setting_name="settings.protocol",
        combobox_options=[],
        disable_on_active_connection=True,
        do_set=lambda cb, v: cb.save_setting(v),
        do_revert=lambda cb: None,
    )


def _combobox_ids(widget):
    model = widget.combobox.get_model()
    return [model[i][1] for i in range(len(model))]  # column 0 is display text, column 1 is id


class TestProtocolGroup:
    def test_returns_protun_group_when_protocol_matches_protun_list(self):
        widget = _make_protocol_widget()
        result = widget.protocol_group("protun-tcp", _PROTUN_PROTOCOLS)
        assert result == ProtocolComboboxWidget.PROTUN_PROTOCOL_GROUP

    def test_returns_generic_group_when_protocol_not_in_protun_list(self):
        widget = _make_protocol_widget()
        result = widget.protocol_group("wireguard", _PROTUN_PROTOCOLS)
        assert result == ProtocolComboboxWidget.GENERIC_PROTOCOL_GROUP


class TestProtocolComboboxWidget:
    def test_protun_checkbox_shown_when_protun_protocols_exist(self):
        widget = _make_protocol_widget()
        assert widget.get_child_at(0, 2) is not None

    def test_no_protun_checkbox_when_protun_protocols_empty(self):
        controller = _make_controller(protun_protocols=[])
        widget = _make_protocol_widget(controller)
        assert widget.get_child_at(0, 2) is None

    def test_combobox_initially_populated_with_generic_protocols(self):
        widget = _make_protocol_widget(current_protocol="wireguard")
        ids = _combobox_ids(widget)
        assert "wireguard" in ids
        assert "protun-tcp" not in ids

    def test_toggling_protun_checkbox_on_repopulates_with_protun_protocols(self):
        widget = _make_protocol_widget()
        checkbox = widget.get_child_at(0, 2).get_first_child()
        checkbox.set_active(True)
        ids = _combobox_ids(widget)
        assert "protun-tcp" in ids
        assert "wireguard" not in ids

    def test_toggling_protun_checkbox_off_repopulates_with_generic_protocols(self):
        widget = _make_protocol_widget()
        checkbox = widget.get_child_at(0, 2).get_first_child()
        checkbox.set_active(True)
        checkbox.set_active(False)
        ids = _combobox_ids(widget)
        assert "wireguard" in ids
        assert "protun-tcp" not in ids

    def test_toggling_protun_checkbox_selects_first_item(self):
        widget = _make_protocol_widget()
        checkbox = widget.get_child_at(0, 2).get_first_child()
        checkbox.set_active(True)
        assert widget.combobox.get_active() == 0

    def test_on_settings_changed_updates_combobox_when_protocol_differs(self):
        widget = _make_protocol_widget(current_protocol="wireguard")
        widget._repopulate_combobox(_GENERIC_PROTOCOLS)
        settings = Mock()
        settings.protocol = "openvpn-tcp"
        widget.on_settings_changed(settings)
        assert widget.combobox.get_active_id() == "openvpn-tcp"
