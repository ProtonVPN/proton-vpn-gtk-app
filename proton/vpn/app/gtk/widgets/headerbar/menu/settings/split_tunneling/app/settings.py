"""
Copyright (c) 2025 Proton AG

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
from __future__ import annotations
from types import ModuleType
from typing import Optional, cast

from gi.repository import Gtk

from proton.vpn.core.settings.split_tunneling import SplitTunnelingMode

from proton.vpn.app.gtk.controller import Controller
from proton.vpn.app.gtk.utils.safe_signal_connect import safe_signal_connect
from proton.vpn.app.gtk.widgets.headerbar.menu.settings.common import SettingName
from proton.vpn.app.gtk.widgets.headerbar.menu.settings.split_tunneling.app.selected_app_list \
    import SelectedAppList
from proton.vpn.app.gtk.widgets.headerbar.menu.settings.split_tunneling.app.app_select_window \
    import AppSelectionWindow
from proton.vpn.app.gtk.widgets.headerbar.menu.settings.split_tunneling.app.data_structures \
    import AppData
from proton.vpn.app.gtk.widgets.headerbar.menu.settings.split_tunneling.app.installed_apps \
    import get_all_installed_apps


LABEL_CONVERSION = {
    SplitTunnelingMode.INCLUDE: "Included apps ",
    SplitTunnelingMode.EXCLUDE: "Excluded apps ",
}


class AppBasedSplitTunnelingSettings(Gtk.Box):  # pylint: disable=too-many-instance-attributes
    """This class contains all settings and configurations
    related to app based split tunneling, serving as an
    entry point to anything related with app based split tunneling.
    """
    def __init__(
        self,
        controller: Controller,
        mode: SplitTunnelingMode,
        setting_path_name_template: str =
        "settings.features.split_tunneling.[mode].app_paths",
        stored_apps: Optional[list[str]] = None,
        selected_app_list: Optional[SelectedAppList] = None,
        installed_apps: Optional[list[AppData]] = None,
        gtk: ModuleType = Gtk,
    ):  # pylint: disable=too-many-arguments
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        self.set_name("split-tunneling-app-based-settings")

        self._controller = controller
        self._setting_path_name_template = setting_path_name_template
        self._mode = mode
        self._stored_apps = stored_apps if stored_apps is not None else \
            self._get_settings()
        self._installed_apps = installed_apps if installed_apps is not None else \
            get_all_installed_apps()
        self._selected_app_list = selected_app_list if selected_app_list is not None else\
            SelectedAppList(self._get_selected_app_list())

        self.gtk = gtk

        self._mode_label = SettingName("")
        self._app_count_label = SettingName("")
        self._add_button = self._create_add_button()
        self._add_app_window: Optional[AppSelectionWindow] = None

        mode_and_app_count_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        mode_and_app_count_box.set_halign(Gtk.Align.START)
        mode_and_app_count_box.append(self._mode_label)
        mode_and_app_count_box.append(self._app_count_label)

        self.append(mode_and_app_count_box)
        self.append(self._selected_app_list)
        self.append(self._add_button)

        self._update_mode_label()
        self._update_app_count_label()

        # We need to track whenever an app is removed or added to the list
        safe_signal_connect(self._selected_app_list, "app-removed", self._on_app_removed)
        safe_signal_connect(
            self._selected_app_list, "app-list-refreshed", self._on_app_list_refreshed
        )

    def _create_add_button(self) -> Gtk.Button:
        button = self.gtk.Button.new_with_label("Add")
        button.set_name("split-tunneling-app-add-button")
        button.add_css_class("secondary")
        safe_signal_connect(button, "clicked", self._on_clicked_add)
        button.set_hexpand(True)
        button.set_halign(Gtk.Align.START)

        return button

    def _on_clicked_add(self, _: Gtk.Button):
        self._add_app_window = AppSelectionWindow(
            title=self._window_title,
            controller=self._controller,
            stored_apps=self._stored_apps,
            installed_apps=self._installed_apps
        )

        safe_signal_connect(
            self._add_app_window, "app-selection-completed", self._on_app_selection_completed
        )
        safe_signal_connect(
            self._add_app_window, "unrealize", self._on_add_app_window_unrealize
        )
        self._add_app_window.present()

    def _on_add_app_window_unrealize(self, _):
        self._add_app_window = None

    @property
    def _window_title(self) -> str:
        return f"Add {LABEL_CONVERSION[self._mode].lower()}"

    def _on_app_selection_completed(
        self, _: AppSelectionWindow,
        selected_apps: list[AppData]
    ):
        """Receive the newly selected apps and issue a refresh to the list
        with the new apps.

        Args:
            _ (AppSelectionWindow): Discarded.
            selected_apps (list[AppData]): List with selected apps to split tunnel.
        """
        # This emits the app-list-refreshed signal
        self._selected_app_list.refresh(selected_apps)

    def update_list_on_new_mode(self, mode: SplitTunnelingMode):
        """Updates the list of split tunneled apps when the mode is switched.

        Args:
            mode (SplitTunnelingMode): the mode that we need to switch to
        """
        self._mode = mode
        self._stored_apps = self._get_settings()
        selected_app_list = self._get_selected_app_list()
        self._selected_app_list.refresh(selected_app_list)
        self._update_mode_label()

    def _on_app_removed(self, _: SelectedAppList, app_data: AppData):
        self._stored_apps = [
            app_exec for app_exec in self._stored_apps
            if app_exec != app_data.executable
        ]
        self._save_and_update_app_count()

    def _on_app_list_refreshed(self, _: SelectedAppList, selected_app_data: list[AppData]):
        self._stored_apps = [app_data.executable for app_data in selected_app_data]
        self._save_and_update_app_count()

    def _save_and_update_app_count(self):
        self._save_settings()
        self._update_app_count_label()

    def _update_app_count_label(self):
        self._app_count_label.set_label(f"({self.amount_of_selected_apps})")

    def _update_mode_label(self):
        self._mode_label.set_label(f"{LABEL_CONVERSION[self._mode]}")

    def _get_selected_app_list(self) -> list[str]:
        return [
            app
            for stored_app_path in self._stored_apps
            for app in self._installed_apps
            if stored_app_path == app.executable
        ]

    def _get_settings(self) -> list[str]:
        return cast(list[str], self._controller.get_setting_attr(self._setting_path_name))

    def _save_settings(self):
        self._controller.save_setting_attr(self._setting_path_name, self._stored_apps)

    @property
    def _setting_path_name(self) -> str:
        return self._setting_path_name_template.replace("[mode]", self._mode.value)

    def get_app_count_label(self) -> str:
        """Returns the label that holds the app counter.

        Returns:
            str:
        """
        return self._app_count_label.get_label()

    def get_mode_label(self) -> str:
        """Returns the label that holds the mode.

        Returns:
            str:
        """
        return self._mode_label.get_label()

    @property
    def amount_of_selected_apps(self) -> int:
        """Returns the amount of selected apps in the list.

        Returns:
            int:
        """
        return len(self._stored_apps)

    def emit_signal_app_removed(self, app_data: AppData):
        """Emits the app-removed signal to the selected app list.
        Mainly used for testing purposes.

        Args:
            app_data (AppData): The app data that was removed.
        """
        self._selected_app_list.emit("app-removed", app_data)

    def emit_signal_app_list_refreshed(self, app_data_list: list[AppData]):
        """Emits the app-list-refreshed signal to the selected app list.
        Mainly used for testing purposes.

        Args:
            app_data_list (list[AppData]): The list of app data that was refreshed.
        """
        self._selected_app_list.emit("app-list-refreshed", app_data_list)

    def click_on_add_button(self):
        """Clicks on the add button."""
        self._add_button.clicked()
