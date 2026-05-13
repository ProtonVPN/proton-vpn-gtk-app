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
from gi.repository import Gtk
from proton.vpn.app.gtk.widgets.headerbar.menu.settings.common import (
    BetaTag, UpgradePlusTag, ToggleWidget, ComboboxWidget, EntryWidget, is_upgrade_required
)
from proton.vpn.core.settings import NetShield


USER_TIER_FREE = 0
USER_TIER_PLUS = 1


def test_upgrade_plus_tag_displays_url_in_window():
    with patch("proton.vpn.app.gtk.widgets.headerbar.menu.settings.common.Gio.AppInfo.launch_default_for_uri") as show_in_browser:
        plus_tag = UpgradePlusTag()
        plus_tag.emit("clicked")
        show_in_browser.assert_called_once_with(plus_tag.URL, None)


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

    @pytest.mark.parametrize(
        "disable_on_active_connection,connection_disconnected,should_widget_be_active", [
            (True, False, False),
            (False, False, True),
            (True, True, True),
            (False, True, True)
        ]
    )
    def test_widget_activation_depending_on_disable_on_active_connection_parameter_and_connection_state(self, disable_on_active_connection, connection_disconnected, should_widget_be_active):
        controller_mock = Mock()
        controller_mock.connection_disconnected = connection_disconnected
        tw = ToggleWidget(
            controller=controller_mock,
            title=self.DEFAULT_TITLE,
            description=self.DEFAULT_DESCRIPTION,
            setting_name=self.DEFAULT_SETTING_NAME,
            disable_on_active_connection=disable_on_active_connection
        )
        assert tw.active == should_widget_be_active

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
            setting_name=self.DEFAULT_SETTING_NAME
        )

        tw._on_switch_state(tw.switch, None)

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

        tw.switch.set_active(control_bool_val)

    @patch("proton.vpn.app.gtk.widgets.headerbar.menu.settings.common.ToggleWidget.save_setting")
    @patch("proton.vpn.app.gtk.widgets.headerbar.menu.settings.common.ToggleWidget.get_setting")
    def test_off_setting_is_saves_to_file_when_calling_it(self, get_setting_mock, save_setting_mock):
        get_setting_mock.return_value = True
        tw = ToggleWidget(
            controller=Mock(),
            title=self.DEFAULT_TITLE,
            description=self.DEFAULT_DESCRIPTION,
            setting_name=self.DEFAULT_SETTING_NAME,
        )

        tw.off()
        save_setting_mock.assert_called_once_with(False)


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

    @pytest.mark.parametrize(
        "disable_on_active_connection,connection_disconnected,should_widget_be_active", [
            (True, False, False),
            (False, False, True),
            (True, True, True),
            (False, True, True)
        ]
    )
    def test_widget_activation_depending_on_disable_on_active_connection_parameter_and_connection_state(self, disable_on_active_connection, connection_disconnected, should_widget_be_active):
        mock_controller = Mock()
        mock_controller.connection_disconnected = connection_disconnected
        cw = ComboboxWidget(
            controller=mock_controller,
            title=self.DEFAULT_TITLE,
            setting_name=self.DEFAULT_SETTING_NAME,
            combobox_options=self.DEFAULT_OPTIONS,
            disable_on_active_connection=disable_on_active_connection
        )
        assert cw.active == should_widget_be_active

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

        def test_callback(combobox: "Gtk.ComboBoxText", _: ComboboxWidget, control=control_bool_val):
            model = combobox.get_model()
            treeiter = combobox.get_active_iter()
            value = model[treeiter][1]
            assert control == value

        cw = ComboboxWidget(
            controller=Mock(),
            title=self.DEFAULT_TITLE,
            setting_name=self.DEFAULT_SETTING_NAME,
            combobox_options=self.DEFAULT_OPTIONS,
            callback=test_callback
        )

        cw.combobox.set_active_id(control_bool_val)

    @patch("proton.vpn.app.gtk.widgets.headerbar.menu.settings.common.ComboboxWidget.save_setting")
    @patch("proton.vpn.app.gtk.widgets.headerbar.menu.settings.common.ComboboxWidget.get_setting")
    def test_off_setting_is_saves_to_file_when_calling_it(self, get_setting_mock, save_setting_mock):
        controller_mock = Mock(name="controller_mock")
        get_setting_mock.return_value = "1"
        cw = ComboboxWidget(
            controller=controller_mock,
            title=self.DEFAULT_TITLE,
            setting_name=self.DEFAULT_SETTING_NAME,
            combobox_options=self.DEFAULT_OPTIONS,
        )
        cw.off()
        save_setting_mock.assert_called_once_with(str(self.DEFAULT_OPTIONS[0][0]))


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

    def test_default_widget_callback_saves_new_received_state(self):
        new_value = "New string to save"
        ew = EntryWidget(
            controller=Mock(),
            title=self.DEFAULT_TITLE,
            description=self.DEFAULT_DESCRIPTION,
            setting_name=self.DEFAULT_SETTING_NAME,
        )
        ew.entry.set_text(new_value)
        ew.entry.emit("changed")
        ew._controller.save_setting_attr.assert_any_call(self.DEFAULT_SETTING_NAME,new_value)

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
        ew.entry.emit("changed")


class TestBetaTag:
    def test_label_is_beta(self):
        assert BetaTag().get_label() == BetaTag.LABEL

    def test_has_beta_tag_css_class(self):
        assert BetaTag().has_css_class("beta-tag")

    def test_is_vertically_centered(self):
        assert BetaTag().get_valign() == Gtk.Align.CENTER


class TestPauseCallback:
    OPTIONS = [("0", "Zero"), ("1", "One"), ("2", "Two")]

    def setup_method(self):
        """Reset state before each test method."""
        self.call_count = 0

    def _make_widget(self, callback):
        controller = Mock()
        controller.get_setting_attr.return_value = "0"
        controller.connection_disconnected = True
        controller.user_tier = USER_TIER_PLUS
        return ComboboxWidget(
            controller=controller,
            title="T",
            setting_name="s",
            combobox_options=self.OPTIONS,
            callback=callback,
        )
    
    def _on_change(self, _combobox):
        self.call_count += 1

    def test_callback_not_fired_while_paused(self):
        cw = self._make_widget(self._on_change)
        with cw.pause_callback():
            cw.combobox.set_active_id("1")

        assert self.call_count == 0

    def test_callback_fires_normally_after_context_exits(self):
        cw = self._make_widget(self._on_change)
        with cw.pause_callback():
            pass
        cw.combobox.set_active_id("1")

        assert self.call_count == 1
