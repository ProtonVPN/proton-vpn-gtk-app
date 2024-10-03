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
from dataclasses import dataclass
from unittest.mock import Mock, PropertyMock, patch
from tests.unit.testing_utils import process_gtk_events
from proton.vpn.app.gtk.widgets.headerbar.menu.settings.common import UpgradePlusTag, ToggleWidget, ComboboxWidget, \
    EntryWidget, is_upgrade_required, get_setting, save_setting
from proton.vpn.core.settings import NetShield


USER_TIER_FREE = 0
USER_TIER_PLUS = 1


@patch("proton.vpn.app.gtk.widgets.headerbar.menu.settings.common.Gdk")
def test_upgrade_plus_tag_displays_url_in_window(gdk_mock):
    gdk_mock.CURRENT_TIME = "mock-time"
    with patch("proton.vpn.app.gtk.widgets.headerbar.menu.settings.common.Gtk.show_uri_on_window") as show_in_browser:
        plus_tag = UpgradePlusTag()
        plus_tag.clicked()
        show_in_browser.assert_called_once_with(None, plus_tag.URL, gdk_mock.CURRENT_TIME)


@pytest.mark.parametrize(
    "requires_subscription_to_be_active,user_tier,expected_result",
    [
        (False, USER_TIER_FREE, False),
        (True, USER_TIER_FREE, True),
        (False, USER_TIER_PLUS, False),
        (True, USER_TIER_PLUS, False),
    ]
)
def test_is_upgrade_required_when_feature_is_paid_and_user_tier_is_free(
    requires_subscription_to_be_active, user_tier, expected_result
):
    _is_upgrade_required = is_upgrade_required(
        requires_subscription_to_be_active=requires_subscription_to_be_active,
        user_tier=user_tier
    )
    assert _is_upgrade_required == expected_result


@dataclass
class MockDataclass:
    test_value: str


@dataclass
class MockSubDataclass:
    another_nest: MockDataclass


@pytest.mark.parametrize(
    "setting_type,nested,setting_path_name,expected_value",
    [
        ("settings", False, "settings.test_value", "Test value"),
        ("settings", False, "settings.test_value", True),
        ("settings", True, "settings.another_nest.test_value", "Test value"),
        ("app_configuration", False, "app_configuration.test_value", "Test value"),
        ("app_configuration", False, "app_configuration.test_value", True),
        ("app_configuration", True, "app_configuration.another_nest.test_value", "Test value"),
    ]
)
def test_get_setting_returns_expected_value_when_getting_value_from_settings(setting_type, nested, setting_path_name, expected_value):
    mock_controller = Mock()

    if nested:
        data = MockSubDataclass(MockDataclass(expected_value))
    else:
        data = MockDataclass(expected_value)

    if setting_type == "settings":
        mock_controller.get_settings.return_value = data
    else:
        mock_controller.get_app_configuration.return_value = data

    received_value = get_setting(controller=mock_controller, setting_path_name=setting_path_name)
    assert received_value == expected_value


def test_save_setting_saves_value_to_disk():
    mock_controller = Mock()
    setting_path_name = "settings.test_value"
    new_value = "New value"
    old_value = "Old value"

    mock_controller.get_settings.return_value = MockDataclass(old_value)

    save_setting(controller=mock_controller, setting_path_name=setting_path_name, new_value=new_value)

    assert mock_controller.save_settings.call_args[0][0].test_value == new_value


def test_save_setting_saves_value_to_disk_from_a_nested_setting_structure():
    mock_controller = Mock()
    setting_path_name = "settings.another_nest.test_value"
    new_value = "New value"
    old_value = "Old value"

    mock_controller.get_settings.return_value = MockSubDataclass(MockDataclass(old_value))

    save_setting(controller=mock_controller, setting_path_name=setting_path_name, new_value=new_value)

    assert mock_controller.save_settings.call_args[0][0].another_nest.test_value == new_value


class TestToggleWidget:
    DEFAULT_SETTING_NAME = "settings.test_value"
    DEFAULT_TITLE = "Test title"
    DEFAULT_DESCRIPTION = "Test description"

    @pytest.mark.parametrize("is_enabled", [True, False])
    @patch("proton.vpn.app.gtk.widgets.headerbar.menu.settings.common.ToggleWidget.get_setting")
    def test_widget_state_is_set_when_it_is_initialized(self, get_setting_mock, is_enabled):
        get_setting_mock.return_value = is_enabled
        tw = ToggleWidget(
            controller=Mock(),
            title=self.DEFAULT_TITLE,
            description=self.DEFAULT_DESCRIPTION,
            setting_name=self.DEFAULT_SETTING_NAME,
        )
        assert tw.switch.get_property("state") == is_enabled

    def test_widget_displays_upgrade_tag_when_user_is_on_free_tier(self):
        mock_controller = Mock()
        mock_controller.user_tier = USER_TIER_FREE
        tw = ToggleWidget(
            controller=mock_controller,
            title=self.DEFAULT_TITLE,
            description=self.DEFAULT_DESCRIPTION,
            setting_name=self.DEFAULT_SETTING_NAME,
            requires_subscription_to_be_active=True
        )
        assert tw.overridden_by_upgrade_tag

    @pytest.mark.parametrize("bool_val", [True])
    @patch("proton.vpn.app.gtk.widgets.headerbar.menu.settings.common.ToggleWidget.save_setting")
    def test_default_widget_callback_saves_new_received_state_when_widget_is_toggled(self, save_setting_mock, bool_val):
        tw = ToggleWidget(
            controller=Mock(),
            title=self.DEFAULT_TITLE,
            description=self.DEFAULT_DESCRIPTION,
            setting_name=self.DEFAULT_SETTING_NAME,
        )

        tw.switch.emit("state-set", bool_val)

        save_setting_mock.assert_called_once_with(bool_val)

    def test_widget_callback_is_received_with_expected_values_when_passing_a_custom_callback(self):
        control_bool_val = True

        def test_callback(_: "Gtk.Switch", received_bool_val, __: ToggleWidget):
            assert received_bool_val == control_bool_val

        tw = ToggleWidget(
            controller=Mock(),
            title=self.DEFAULT_TITLE,
            description=self.DEFAULT_DESCRIPTION,
            setting_name=self.DEFAULT_SETTING_NAME,
            callback=test_callback
        )

        tw.switch.emit("state-set", control_bool_val)


class TestComboboxWidget:
    DEFAULT_SETTING_NAME = "settings.test_value"
    DEFAULT_TITLE = "Test title"
    DEFAULT_OPTIONS = [("0", "Option Zero"), ("1", "Option One"), ("2", "Option Two")]

    @pytest.mark.parametrize("selected_option", ["0", "1", "2"])
    @patch("proton.vpn.app.gtk.widgets.headerbar.menu.settings.common.ComboboxWidget.get_setting")
    def test_widget_option_is_set_when_it_is_initialized(self, get_setting_mock, selected_option):
        get_setting_mock.return_value = selected_option
        cw = ComboboxWidget(
            controller=Mock(),
            title=self.DEFAULT_TITLE,
            setting_name=self.DEFAULT_SETTING_NAME,
            combobox_options=self.DEFAULT_OPTIONS
        )
        assert cw.combobox.get_active_id() == selected_option

    def test_widget_is_disabled_when_there_is_an_active_connection_upon_being_initialized(self):
        mock_controller = Mock()
        mock_controller.is_connection_disconnected = False
        cw = ComboboxWidget(
            controller=mock_controller,
            title=self.DEFAULT_TITLE,
            setting_name=self.DEFAULT_SETTING_NAME,
            combobox_options=self.DEFAULT_OPTIONS,
            disable_on_active_connection=True
        )
        assert not cw.active

    def test_widget_displays_upgrade_tag_when_user_is_on_free_tier(self):
        mock_controller = Mock()
        mock_controller.user_tier = USER_TIER_FREE
        cw = ComboboxWidget(
            controller=mock_controller,
            title=self.DEFAULT_TITLE,
            setting_name=self.DEFAULT_SETTING_NAME,
            combobox_options=self.DEFAULT_OPTIONS,
            requires_subscription_to_be_active=True
        )
        assert cw.overridden_by_upgrade_tag

    @pytest.mark.parametrize("new_id", ["2"])
    @patch("proton.vpn.app.gtk.widgets.headerbar.menu.settings.common.ComboboxWidget.save_setting")
    def test_default_widget_callback_saves_new_received_option_when_combobox_is_changed(self, save_setting_mock, new_id):
        cw = ComboboxWidget(
            controller=Mock(),
            title=self.DEFAULT_TITLE,
            setting_name=self.DEFAULT_SETTING_NAME,
            combobox_options=self.DEFAULT_OPTIONS,
        )
        cw.combobox.set_active_id(new_id)
        save_setting_mock.assert_called_once_with(new_id)

    def test_widget_callback_is_received_with_expected_values_when_passing_a_custom_callback(self):
        control_bool_val = "1"

        def test_callback(combobox: "Gtk.ComboBoxText", _: ComboboxWidget):
            model = combobox.get_model()
            treeiter = combobox.get_active_iter()
            value = model[treeiter][1]
            assert control_bool_val == value

        cw = ComboboxWidget(
            controller=Mock(),
            title=self.DEFAULT_TITLE,
            setting_name=self.DEFAULT_SETTING_NAME,
            combobox_options=self.DEFAULT_OPTIONS,
            callback=test_callback
        )

        cw.combobox.set_active_id(control_bool_val)


class TestEntryWidget:
    DEFAULT_SETTING_NAME = "settings.test_value"
    DEFAULT_TITLE = "Test title"
    DEFAULT_DESCRIPTION = "Test description"

    @patch("proton.vpn.app.gtk.widgets.headerbar.menu.settings.common.EntryWidget.get_setting")
    def test_widget_entry_is_set_when_it_is_initialized(self, get_setting_mock):
        initial_value = "New Option"
        get_setting_mock.return_value = initial_value
        ew = EntryWidget(
            controller=Mock(),
            title=self.DEFAULT_TITLE,
            description=self.DEFAULT_DESCRIPTION,
            setting_name=self.DEFAULT_SETTING_NAME,
        )
        assert ew.entry.get_text() == initial_value

    def test_widget_displays_upgrade_tag_when_user_is_on_free_tier(self):
        mock_controller = Mock()
        mock_controller.user_tier = USER_TIER_FREE
        ew = EntryWidget(
            controller=mock_controller,
            title=self.DEFAULT_TITLE,
            description=self.DEFAULT_DESCRIPTION,
            setting_name=self.DEFAULT_SETTING_NAME,
            requires_subscription_to_be_active=True
        )
        assert ew.overridden_by_upgrade_tag

    @pytest.mark.parametrize("new_value", ["New string to save"])
    @patch("proton.vpn.app.gtk.widgets.headerbar.menu.settings.common.EntryWidget.save_setting")
    def test_default_widget_callback_saves_new_received_state_when_leaving_widget_focus(self, save_setting_mock, new_value):
        ew = EntryWidget(
            controller=Mock(),
            title=self.DEFAULT_TITLE,
            description=self.DEFAULT_DESCRIPTION,
            setting_name=self.DEFAULT_SETTING_NAME,
        )
        ew.entry.set_text(new_value)
        ew.entry.emit("focus-out-event", None)

        save_setting_mock.assert_called_once_with(new_value)

    def test_widget_callback_is_received_with_expected_values_when_passing_a_custom_callback(self):
        control_bool_val = "New test string"

        def test_callback(gtk_widget: "Gtk.Switch", _: "Gdk.EventFocus", __: EntryWidget):
            assert gtk_widget.get_text() == control_bool_val

        ew = EntryWidget(
            controller=Mock(),
            title=self.DEFAULT_TITLE,
            description=self.DEFAULT_DESCRIPTION,
            setting_name=self.DEFAULT_SETTING_NAME,
            callback=test_callback
        )

        ew.entry.set_text(control_bool_val)
        ew.entry.emit("focus-out-event", None)
