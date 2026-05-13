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

from typing import Optional
from gi.repository import Gtk, GObject

from proton.vpn.app.gtk.utils.safe_signal_connect import safe_signal_connect
from proton.vpn.app.gtk.widgets.headerbar.menu.settings.split_tunneling.app.data_structures \
    import AppRowWithRemoveButton, AppData


class SelectedAppList(Gtk.ScrolledWindow):
    """A scrolled window that contains the list of split tunneling apps.

    It modifies the UI based on the provided input. It does not save any
    data to disk.
    """
    MAX_AMOUNT_OF_APPS_TO_DISPLAY = 6
    APP_ROW_SIZE = 35

    def __init__(self, apps_to_add: Optional[list[AppData]] = None):
        super().__init__()
        self.set_name("selected-app-list")

        self.main_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self._data_mapping: dict[AppData, AppRowWithRemoveButton] = {}

        viewport = Gtk.Viewport()
        viewport.add_css_class("viewport-frame")
        viewport.set_child(self.main_container)

        self.set_propagate_natural_width(True)
        self.set_child(viewport)

        self.refresh(apps_to_add)

    def refresh(self, selected_apps: list[AppData]):
        """Refreshes the entire list.
        This method is mainly used when adding new apps,
        so that the entire list can be refreshed.

        Args:
            selected_apps (list[AppData])
        """
        list_has_been_modified = False

        for app_data in list(self._data_mapping.keys()):
            # This app was already previously selected, we can skip it
            if app_data in selected_apps:
                continue

            # App was deselected, has to be removed
            list_has_been_modified = True
            self.main_container.remove(self._data_mapping.pop(app_data))

        for app_data in selected_apps:
            # If selected app exists in existing_apps then we don't add it
            if app_data in self._data_mapping:
                continue

            # Only add if child does not exist already
            list_has_been_modified = True
            app_row = self._generate_app_row(app_data)
            self.main_container.append(app_row)
            self._data_mapping[app_data] = app_row

        # Resize view only if list has been modified
        if not list_has_been_modified:
            return

        self._update_scrolled_window_size()
        self.emit("app-list-refreshed", selected_apps)

    def _remove_app(self, app_row: AppRowWithRemoveButton):
        """Remove app from list and notify once it's removed.

        Args:
            app_row (AppData)
        """
        app_data = app_row.app_data
        self.main_container.remove(self._data_mapping.pop(app_data))
        self._update_scrolled_window_size()
        self.emit("app-removed", app_data)

    def _update_scrolled_window_size(self):
        number_of_apps = len(self._data_mapping)
        no_scroll = number_of_apps < self.MAX_AMOUNT_OF_APPS_TO_DISPLAY
        max_size = self.MAX_AMOUNT_OF_APPS_TO_DISPLAY * self.APP_ROW_SIZE
        current_app_based_size = number_of_apps * self.APP_ROW_SIZE

        self.set_propagate_natural_height(no_scroll)
        self.set_min_content_height(
            max_size if current_app_based_size > max_size else current_app_based_size
        )

    def _generate_app_row(self, app_data: AppData) -> AppRowWithRemoveButton:
        app_row = AppRowWithRemoveButton.build(app_data)
        safe_signal_connect(app_row, "remove-app", self._remove_app)
        return app_row

    @GObject.Signal(name="app-removed", arg_types=(object,))
    def app_removed(self, app_data: AppData):
        """Signal emitted when an app is removed from the list.

        Args:
          app(AppData)
        """

    @GObject.Signal(name="app-list-refreshed", arg_types=[object,])
    def app_list_refreshed(self, selected_app_data: list[AppData]):
        """Signal emitted after the list has been fully refreshed.

        Args:
          app(AppData)
        """
