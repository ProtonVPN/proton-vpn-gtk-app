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

from gi.repository import Gtk

from proton.vpn.core.settings.split_tunneling import SplitTunnelingMode

from proton.vpn.app.gtk.controller import Controller
from proton.vpn.app.gtk.widgets.headerbar.menu.settings.common import \
    SettingName
from proton.vpn.app.gtk.widgets.headerbar.menu.settings.split_tunneling.app.selected_app_list \
    import SelectedAppList
from proton.vpn.app.gtk.widgets.headerbar.menu.settings.split_tunneling.app.app_select_window \
    import AppSelectionWindow
from proton.vpn.app.gtk.widgets.headerbar.menu.settings.split_tunneling.app.data_structures \
    import AppData
from proton.vpn.app.gtk.widgets.headerbar.menu.settings.split_tunneling.app.util \
    import _get_all_installed_apps


LABEL_CONVERSION = {
    SplitTunnelingMode.INCLUDE: "Included",
    SplitTunnelingMode.EXCLUDE: "Excluded",
}


class AppBasedSplitTunnelingSettings(Gtk.Box):  # pylint: disable=too-many-instance-attributes
    """This class contains all settings and configurations
    related to app based split tunneling, serving as an
    entry point to anything related with app based split tunneling.
    """
    def __init__(
        self,
        controller: Controller,
        setting_path_name: str = "settings.features.split_tunneling.config.app_paths",
        mode: SplitTunnelingMode = SplitTunnelingMode.EXCLUDE,
        stored_apps: list[str] = None,
        selected_app_list: SelectedAppList = None,
        installed_apps: list[AppData] = None,
        gtk: Gtk = Gtk,
    ):  # pylint: disable=too-many-arguments
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        self.set_name("split-tunneling-app-based-settings")

        self._controller = controller
        self._settings_path_name = setting_path_name
        self._mode = mode
        self._stored_apps = stored_apps if stored_apps is not None else \
            self._controller.get_setting_attr(self._settings_path_name)
        self._installed_apps = installed_apps if installed_apps is not None else \
            _get_all_installed_apps()
        self._selected_app_list = selected_app_list if selected_app_list is not None else\
            SelectedAppList([
                    app
                    for stored_app_path in self._stored_apps
                    for app in self._installed_apps
                    if stored_app_path == app.executable
            ])

        self.gtk = gtk

        self._setting_name = SettingName("")
        self._add_button = self._create_add_button()

        self.add(self._setting_name)
        self.add(self._selected_app_list)
        self.add(self._add_button)

        self._update_setting_name()

        # We need to track whenever an app is removed or added to the list
        self._selected_app_list.connect("app-removed", self._on_app_removed)
        self._selected_app_list.connect("app-list-refreshed", self._on_app_list_refreshed)

    def _create_add_button(self) -> Gtk.Button:
        button = self.gtk.Button.new_with_label("Add")
        button.set_name("split-tunneling-app-add-button")
        button.get_style_context().add_class("secondary")
        button.connect("clicked", self._on_clicked_add)
        button.set_hexpand(True)
        button.set_halign(Gtk.Align.START)

        return button

    def _on_clicked_add(self, _: Gtk.Button):
        add_app_window = AppSelectionWindow(
            title=f"Add {self._mode.value}d apps",
            controller=self._controller,
            stored_apps=self._stored_apps,
            installed_apps=self._installed_apps
        )

        add_app_window.connect("app-selection-completed", self._on_app_selection_completed)
        add_app_window.present()

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
        self._update_setting_name()

    def _update_setting_name(self):
        label = f"{LABEL_CONVERSION[self._mode]} Apps ({self.amount_of_displayed_apps})"
        self._setting_name.set_label(label)

    def _get_settings(self) -> list[str]:
        return self._controller.get_setting_attr(self._settings_path_name)

    def _save_settings(self):
        self._controller.save_setting_attr(self._settings_path_name, self._stored_apps)

    def get_app_count_label(self) -> str:
        """Returns the label that holds the app counter.

        Returns:
            str:
        """
        return self._setting_name.get_label()

    @property
    def amount_of_displayed_apps(self) -> int:
        """Returns the amount of displayed apps in the list.

        Returns:
            int:
        """
        return len(self._stored_apps)

    def _emit_signal_app_removed(self, app_data: AppData):
        self._selected_app_list.emit("app-removed", app_data)

    def _emit_signal_app_list_refreshed(self, app_data_list: list[AppData]):
        self._selected_app_list.emit("app-list-refreshed", app_data_list)

    def _click_on_add_button(self):
        self._add_button.clicked()
