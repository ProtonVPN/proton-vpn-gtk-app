"""
This module contains common objects that are used by different settings types.


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
from typing import List, Tuple, Callable, Any
from gi.repository import Gtk, Gdk
from proton.vpn.app.gtk.controller import Controller
from proton.vpn.app.gtk.widgets.main.confirmation_dialog \
    import ConfirmationDialog, show_confirmation_dialog


RECONNECT_MESSAGE = "Please establish a new VPN connection for "\
        "changes to take effect."


class CategoryHeader(Gtk.Label):
    """Header that is used to seperate between setting types, such as
    Features, Connection, etc."""
    def __init__(self, label: str):
        super().__init__(label=label)
        self.set_halign(Gtk.Align.START)
        style_context = self.get_style_context()
        style_context.add_class("heading")


class ReactiveSetting:  # pylint: disable=too-few-public-methods
    """Base class for reactive settings that need to be updated when settings change."""
    def on_settings_changed(self, _settings):
        """Method that is called when settings are changed.
        This is used to update the widget when settings change."""
        raise NotImplementedError("This method should be implemented in subclasses.")


class ReactiveSettingContainer:  # pylint: disable=too-few-public-methods
    """Base class for containers that hold reactive settings."""
    def get_children(self):
        """Returns the children of this container, normally implemented by
        the Gtk.Container class, it must be implemented in order
        for this class to work."""

        raise NotImplementedError(
            "This method should be implemented.")

    def on_settings_changed(self, settings):
        """Method that is called when settings are changed.
        This is used to update the widget when settings change."""
        for child in self.get_children():
            if isinstance(child, ReactiveSetting):
                child.on_settings_changed(settings)


class BaseCategoryContainer(Gtk.Box):
    """Base container class that is used to group common settings.

    Mostly a helper class to remove the necessity of writing boilerplate
    styling code in each category container.
    """
    def __init__(self, category_name: str):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)

        self.get_style_context().add_class("setting-category")
        self.set_halign(Gtk.Align.FILL)
        self.set_spacing(15)

        self.pack_start(CategoryHeader(category_name), False, False, 0)


class UpgradePlusTag(Gtk.Button):
    """ Using normal button instead of LinkButton mainly
    because of styling. LinkButtons usually have very ugly UI,
    and all they do is emit `::activate-link` which
    just calls `Gtk.show_uri_on_window`.

    Source: https://lazka.github.io/pgi-docs/Gtk-3.0/classes/LinkButton.html
    """
    LABEL = "VPN Plus"
    URL = "https://protonvpn.com/pricing"

    def __init__(self):
        super().__init__(label=self.LABEL)
        self.get_style_context().add_class("upgrade-tag")
        self.get_style_context().add_class("heading")
        self.connect("clicked", self._on_button_clicked)

    def _on_button_clicked(self, _):
        Gtk.show_uri_on_window(
            None,
            self.URL,
            Gdk.CURRENT_TIME
        )


class SettingName(Gtk.Label):
    """Label used to identify a setting."""
    def __init__(self, label: str, bold: bool = False):
        if bold:
            label = f"<b>{label}</b>"

        super().__init__(label=label)
        self.set_halign(Gtk.Align.START)
        self.set_hexpand(True)
        self.set_use_markup(True)

    @property
    def enabled(self) -> bool:
        """Returns if the label is enabled."""
        return self.get_property("sensitive")

    @enabled.setter
    def enabled(self, new_value: bool):
        """Sets if the label should be enabled."""
        self.set_property("sensitive", new_value)


class SettingDescription(Gtk.Label):
    """Label used to desribe a setting."""
    def __init__(self, label: str):
        super().__init__(label=label)
        self.get_style_context().add_class("dim-label")
        self.set_line_wrap(True)
        self.set_max_width_chars(1)
        self.set_property("xalign", 0)
        self.set_hexpand(True)
        self.set_use_markup(True)


def is_upgrade_required(requires_subscription_to_be_active: bool, user_tier: int) -> bool:
    """Returns if an upgrade is required for a certain setting."""
    return requires_subscription_to_be_active and user_tier < 1


class CustomButton(Gtk.Grid):
    """Custom button setting."""
    def __init__(  # pylint: disable=too-many-arguments
        self,
        title: str,
        description: str,
        button_label: str,
        on_click_callback: Callable,
        requires_subscription_to_be_active: bool = False,
        bold_title: bool = False
    ):
        super().__init__()
        self._apply_grid_styles()
        self._requires_subscription_to_be_active = requires_subscription_to_be_active
        self.label = SettingName(title, bold=bold_title)
        self.description = SettingDescription(description)
        self.button = self._build_button(button_label, on_click_callback)
        self._build_ui()

    def _build_button(self, button_label: str, on_click_callback: Callable) -> Gtk.Button:
        button = Gtk.Button()
        button.set_label(button_label)
        button.connect("clicked", on_click_callback)
        return button

    def _build_ui(self):
        """Builds the UI depending if an upgrade is required or not."""
        if self._requires_subscription_to_be_active:
            self.button = UpgradePlusTag()

        self.attach(self.label, 0, 0, 1, 1)

        # Style interactive_object so it's always aligned
        self.button.set_hexpand(True)
        self.button.set_halign(Gtk.Align.END)

        self.attach(self.button, 1, 0, 1, 1)

        if self.description:
            self.attach(self.description, 0, 1, 2, 1)

    def _apply_grid_styles(self):
        self.get_style_context().add_class("setting-item")
        self.set_halign(Gtk.Align.FILL)
        self.set_row_spacing(10)
        self.set_column_spacing(100)


class ToggleWidget(Gtk.Grid):  # pylint: disable=too-many-instance-attributes
    """Default toggle widget."""
    def __init__(  # pylint: disable=too-many-arguments
        self,
        controller: Controller,
        title: str,
        description: str,
        setting_name: str,
        requires_subscription_to_be_active: bool = False,
        callback: Callable = None,
        disable_on_active_connection: bool = False,
        enabled: bool = None
    ):
        super().__init__()
        self._apply_grid_styles()
        self._controller = controller
        self._setting_name = setting_name
        self._callback = callback
        self._requires_subscription_to_be_active = requires_subscription_to_be_active
        self._disable_on_active_connection = disable_on_active_connection
        self._enabled = enabled

        self.label = SettingName(title)
        self.description = SettingDescription(description)
        self.switch = self._build_switch()

        self._build_ui()

    @property
    def active(self) -> bool:
        """Returns if the widget is active or not."""
        return self.get_property("sensitive")

    @active.setter
    def active(self, new_value: bool):
        """Set if the widget should be active or not."""
        self.set_property("sensitive", new_value)

    def get_setting(self) -> bool:
        """Shortcut property that returns the current setting"""
        return self._controller.get_setting_attr(self._setting_name)

    def save_setting(self, new_value: bool):
        """Shortcut property that sets the new setting and stores to disk."""
        self._controller.save_setting_attr(self._setting_name, new_value)

    @property
    def overridden_by_upgrade_tag(self) -> bool:
        """Returns if the the upgrade tag has overridden original interactive
        object."""
        return isinstance(self.switch, UpgradePlusTag)

    def set_tooltip(self, tooltip_text: str):
        """Set a tooltip to this row."""
        self.set_has_tooltip(True)
        self.set_tooltip_text(tooltip_text)

    def _apply_grid_styles(self):
        self.get_style_context().add_class("setting-item")
        self.set_halign(Gtk.Align.FILL)
        self.set_row_spacing(10)
        self.set_column_spacing(100)

    def _build_switch(self) -> Gtk.Switch:
        switch = Gtk.Switch()
        if self._enabled is None:
            self._enabled = self.get_setting()
        switch.set_state(self._enabled)

        switch.connect("notify::active", self._on_switch_state)

        return switch

    def _build_ui(self):
        """Builds the UI depending if an upgrade is required or not."""
        if self._is_upgrade_required:
            self.switch = UpgradePlusTag()

        self.attach(self.label, 0, 0, 1, 1)

        # Style interactive_object so it's always aligned
        self.switch.set_hexpand(True)
        self.switch.set_halign(Gtk.Align.END)

        self.attach(self.switch, 1, 0, 1, 1)

        if self.description:
            self.attach(self.description, 0, 1, 2, 1)

        if (not self._controller.is_connection_disconnected  # noqa: E501 # pylint: disable=line-too-long # nosemgrep: python.lang.maintainability.is-function-without-parentheses.is-function-without-parentheses
                and self._disable_on_active_connection):
            self.active = False

    def _on_switch_state(self, switch, _gparam):
        new_value = switch.get_state()
        if self._callback:
            self._callback(self, new_value, self)
        else:
            self.save_setting(new_value)

    @property
    def _is_upgrade_required(self) -> bool:
        """Returns if an upgrade is required for a given setting."""
        return is_upgrade_required(
            self._requires_subscription_to_be_active,
            self._controller.user_tier
        )

    def off(self):
        """Shortcut to toggle the widget to disabled."""
        self.switch.set_state(False)


class ConflictableToggleWidget(ToggleWidget):  # pylint: disable=too-many-instance-attributes
    """
    Toggle widget that can handle conflicts when toggling the switch.
    It will show a confirmation dialog if the toggle is in conflict with
    other settings.
    """
    def __init__(  # pylint: disable=too-many-arguments
        self,
        controller: Controller,
        title: str,
        description: str,
        setting_name: str,
        do_set: Callable[[ToggleWidget, bool], None],
        do_revert: Callable[[ToggleWidget], None],
        requires_subscription: bool = False,
        disable_on_active_connection: bool = False,
        enabled: bool = None,
        conflict_resolver: Callable[[str, Any], str] = None,
    ):
        super().__init__(
            controller=controller, title=title,
            description=description, setting_name=setting_name,
            requires_subscription_to_be_active=requires_subscription,
            callback=self._on_switch_button_toggle,
            disable_on_active_connection=disable_on_active_connection,
            enabled=enabled)
        self.do_set = do_set
        self.do_revert = do_revert

        # Allow to pass a custom conflict resolver
        if conflict_resolver is None:
            conflict_resolver = controller.setting_attr_has_conflict
        self._conflict_resolver = conflict_resolver

    def _on_switch_button_toggle(self, _, new_value: bool, __):

        if conflict := self._conflict_resolver(self._setting_name, new_value):

            def confirm_change(dialog: ConfirmationDialog, response: int):
                if response == Gtk.ResponseType.YES:
                    # do_set can be any callable that takes
                    # (ToggleWidget, int) as arguments so although it looks
                    # like we are calling a method on self, we are actually
                    # calling the method that was passed to the constructor.
                    # This allows for instantiating this class with different
                    # do_set and do_revert methods without having to
                    # subclass it.
                    #
                    # We are passing `self` as the first argument
                    # because the do_set method expects a ToggleWidget.
                    self.do_set(self, new_value)
                else:
                    # Similarly to above, we are calling the
                    # do_revert method that was passed to the constructor,
                    # it's not a method of this class.
                    # This is why we are passing `self` as the first argument.
                    self.do_revert(self)

                # We cant just close the dialog, instead we destroy it
                # directly.
                dialog.destroy()

            show_confirmation_dialog(
                self.get_toplevel(),
                title="",
                question=conflict.label,
                clarification=conflict.description,
                yes_text="_Yes",
                no_text="_Cancel",
                callback_result=confirm_change
            )
        else:
            self.do_set(self, new_value)


class ComboboxWidget(Gtk.Grid):  # pylint: disable=too-many-instance-attributes
    """Default combobox text widget."""
    def __init__(  # pylint: disable=too-many-arguments
        self,
        controller: Controller,
        title: str,
        setting_name: str,
        combobox_options: List[Tuple[int, str]],
        description: str = None,
        requires_subscription_to_be_active: bool = False,
        callback: Callable = None,
        disable_on_active_connection: bool = False
    ):
        super().__init__()
        self._apply_grid_styles()
        self._controller = controller
        self._setting_name = setting_name
        self._combobox_options = combobox_options
        self._callback = callback
        self._requires_subscription_to_be_active = requires_subscription_to_be_active
        self.label = SettingName(title)
        self.description = None if not description else SettingDescription(description)
        self._disable_on_active_connection = disable_on_active_connection
        self.combobox = self._build_combobox()
        self._build_ui()

    @property
    def active(self) -> bool:
        """Returns if the widget is active or not."""
        return self.get_property("sensitive")

    @active.setter
    def active(self, new_value: bool):
        """Set if the widget should be active or not."""
        self.set_property("sensitive", new_value)

    def get_setting(self) -> str:
        """Shortcut property that returns the current setting"""
        return str(self._controller.get_setting_attr(self._setting_name))

    def save_setting(self, new_value: int):
        """Shortcut property that sets the new setting and stores to disk."""
        self._controller.save_setting_attr(self._setting_name, new_value)

    @property
    def overridden_by_upgrade_tag(self) -> bool:
        """Returns if the the upgrade tag has overridden original interactive
        object."""
        return isinstance(self.combobox, UpgradePlusTag)

    def set_tooltip(self, tooltip_text: str):
        """Set a tooltip to this row."""
        self.set_has_tooltip(True)
        self.set_tooltip_text(tooltip_text)

    def _apply_grid_styles(self):
        self.get_style_context().add_class("setting-item")
        self.set_halign(Gtk.Align.FILL)
        self.set_row_spacing(10)
        self.set_column_spacing(100)

    def _build_combobox(self) -> Gtk.Switch:
        combobox = Gtk.ComboBoxText()
        for value, display in self._combobox_options:
            combobox.append(str(value), display)

        combobox.set_entry_text_column(1)
        combobox.set_active_id(self.get_setting())

        if self._callback:
            combobox.connect("changed", self._callback, self)
        else:
            combobox.connect("changed", self._on_combobox_change)

        if (not self._controller.is_connection_disconnected  # noqa: E501 # pylint: disable=line-too-long # nosemgrep: python.lang.maintainability.is-function-without-parentheses.is-function-without-parentheses
                and self._disable_on_active_connection):
            self.active = False

        return combobox

    def _build_ui(self):
        """Builds the UI depending if an upgrade is required or not."""
        if self._is_upgrade_required:
            self.combobox = UpgradePlusTag()

        self.attach(self.label, 0, 0, 1, 1)

        # Style interactive_object so it's always aligned
        self.combobox.set_hexpand(True)
        self.combobox.set_halign(Gtk.Align.END)

        self.attach(self.combobox, 1, 0, 1, 1)

        if self.description:
            self.attach(self.description, 0, 1, 2, 1)

    @property
    def _is_upgrade_required(self) -> bool:
        """Returns if an upgrade is required for a given setting."""
        return is_upgrade_required(
            self._requires_subscription_to_be_active,
            self._controller.user_tier
        )

    def _on_combobox_change(self, combobox: Gtk.ComboBox):
        model = combobox.get_model()
        treeiter = combobox.get_active_iter()
        value = model[treeiter][1]
        self.save_setting(value)

    def off(self):
        """Shortcut to set the combobox to disabled."""
        self.combobox.set_active_id(str(0))


class ConflictableComboboxWidget(ComboboxWidget):
    """
    Combobox widget that can handle conflicts when changing the combobox value.
    It will show a confirmation dialog if the combobox change is in conflict with
    other settings.
    """
    def __init__(  # pylint: disable=too-many-arguments
        self,
        controller: Controller,
        title: str,
        setting_name: str,
        combobox_options: List[Tuple[int, str]],
        do_set: Callable[[ComboboxWidget, int], None],
        do_revert: Callable[[ComboboxWidget], None],
        description: str = None,
        requires_subscription: bool = False,
        disable_on_active_connection: bool = False
    ):
        super().__init__(
            controller=controller, title=title, setting_name=setting_name,
            combobox_options=combobox_options, description=description,
            requires_subscription_to_be_active=requires_subscription,
            callback=self._on_conflictable_combobox_change,
            disable_on_active_connection=disable_on_active_connection
        )
        self._do_set = do_set
        self._do_revert = do_revert

    def _on_conflictable_combobox_change(
            self, combobox_text_widget, _combobox: Gtk.ComboBox):
        new_value = combobox_text_widget.get_active_text()

        if conflict := self._controller.setting_attr_has_conflict(
                self._setting_name, new_value):

            def confirm_change(dialog: ConfirmationDialog, response: int):
                if response == Gtk.ResponseType.YES:
                    # do_set can be any callable that takes
                    # (ComboboxWidget, int) as arguments so although it looks
                    # like we are calling a method on self, we are actually
                    # calling the method that was passed to the constructor.
                    # This allows for instantiating this class with different
                    # do_set and do_revert methods without having to
                    # subclass it.
                    #
                    # We are passing `self` as the first argument
                    # because the do_set method expects a ComboboxWidget.
                    self._do_set(self, new_value)
                else:
                    # Similarly to above, we are calling the
                    # do_revert method that was passed to the constructor,
                    # it's not a method of this class.
                    # This is why we are passing `self` as the first argument.
                    self._do_revert(self)

                # We cant just close the dialog, instead we destroy it
                # directly.
                dialog.destroy()

            show_confirmation_dialog(
                self.get_toplevel(),
                title="",
                question=conflict.label,
                clarification=conflict.description,
                yes_text="_Yes",
                no_text="_Cancel",
                callback_result=confirm_change
            )
        else:
            self._do_set(self, new_value)


class EntryWidget(Gtk.Grid):
    """Default entry widget."""
    def __init__(  # pylint: disable=too-many-arguments
        self,
        controller: Controller,
        title: str,
        setting_name: str,
        description: str,
        callback: Callable = None,
        requires_subscription_to_be_active: bool = False,
    ):
        super().__init__()
        self._apply_grid_styles()
        self._controller = controller
        self._setting_name = setting_name
        self._callback = callback
        self._requires_subscription_to_be_active = requires_subscription_to_be_active
        self.label = SettingName(title)
        self.description = SettingDescription(description)
        self.entry = self._build_entry()
        self._build_ui()

    @property
    def active(self) -> bool:
        """Returns if the widget is active or not."""
        return self.get_property("sensitive")

    @active.setter
    def active(self, new_value: bool):
        """Set if the widget should be active or not."""
        self.set_property("sensitive", new_value)

    def get_setting(self) -> bool:
        """Shortcut property that returns the current setting"""
        return self._controller.get_setting_attr(self._setting_name)

    def save_setting(self, new_value: bool):
        """Shortcut property that sets the new setting and stores to disk."""
        self._controller.save_setting_attr(self._setting_name, new_value)

    @property
    def overridden_by_upgrade_tag(self) -> bool:
        """Returns if the the upgrade tag has overridden original interactive
        object."""
        return isinstance(self.entry, UpgradePlusTag)

    def set_tooltip(self, tooltip_text: str):
        """Set a tooltip to this row."""
        self.set_has_tooltip(True)
        self.set_tooltip_text(tooltip_text)

    def _apply_grid_styles(self):
        self.get_style_context().add_class("setting-item")
        self.set_halign(Gtk.Align.FILL)
        self.set_row_spacing(10)
        self.set_column_spacing(100)

    def _build_entry(self) -> Gtk.Entry:
        entry = Gtk.Entry()
        value = self.get_setting()
        if value is None:
            value = "Off"

        entry.set_text(str(value))
        if self._callback:
            entry.connect("focus-out-event", self._callback, self)
        else:
            entry.connect("focus-out-event", self._on_focus_out_event)

        return entry

    def _build_ui(self):
        """Builds the UI depending if an upgrade is required or not."""
        if self._is_upgrade_required:
            self.entry = UpgradePlusTag()

        self.attach(self.label, 0, 0, 1, 1)

        # Style interactive_object so it's always aligned
        self.entry.set_hexpand(True)
        self.entry.set_halign(Gtk.Align.END)

        self.attach(self.entry, 1, 0, 1, 1)

        if self.description:
            self.attach(self.description, 0, 1, 2, 1)

    def _on_focus_out_event(self, gtk_widget: Gtk.Entry, _: Gdk.EventFocus):
        self.save_setting(gtk_widget.get_text())

    @property
    def _is_upgrade_required(self) -> bool:
        """Returns if an upgrade is required for a given setting."""
        return is_upgrade_required(
            self._requires_subscription_to_be_active,
            self._controller.user_tier
        )
