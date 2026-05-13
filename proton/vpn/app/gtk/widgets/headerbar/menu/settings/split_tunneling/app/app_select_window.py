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
from typing import cast
from gi.repository import Gtk, GObject


from proton.vpn.app.gtk.controller import Controller
from proton.vpn.app.gtk.utils.safe_signal_connect import safe_signal_connect
from proton.vpn.app.gtk.widgets.headerbar.menu.settings.split_tunneling.app.data_structures \
    import AppRowWithCheckbox, AppData


class AppSelectionWindow(Gtk.Window):
    """This widget displays all available apps,
    and pre-check any already selected apps. Once the user
    clicks on `Done`, all data is transferred back to
    `AppBasedSplitTunnelingSettings` for further processing,
    both for UI updates and also storing data to disk.
    """
    def __init__(
        self,
        title: str,
        controller: Controller,
        stored_apps: list[str],
        installed_apps: list[AppData],
        gtk: ModuleType = Gtk
    ):  # pylint: disable=too-many-arguments
        super().__init__()
        self.set_modal(True)
        self.set_title(title)
        self.set_default_size(600, 500)
        self.set_name("split-tunneling-app-selection-window")

        self.gtk = gtk
        self._controller = controller
        self._stored_apps = stored_apps
        self._installed_apps = installed_apps

        # Can't use self.container as that seems to be a non-writable property,
        # probably reserved by Gtk.
        self.main_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.content_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)

        self._create_elastic_window()

        safe_signal_connect(self, "realize", self._build_ui)

    def _create_elastic_window(self):
        """This allows for the content to be always centered and expand or contract
        based on window size.

        The reason we use two containers is mainly due to the notification bar, as this
        way the notification will span across the entire window while only the
        settings will be centered.
        """
        viewport = Gtk.Viewport.new(None, None)
        viewport.add_css_class("viewport-frame")
        viewport.set_child(self.content_container)

        scrolled_window = Gtk.ScrolledWindow.new()
        scrolled_window.set_propagate_natural_height(True)
        scrolled_window.set_min_content_height(200)
        scrolled_window.set_min_content_width(400)
        scrolled_window.set_child(viewport)

        self.main_container.append(scrolled_window)

        self.set_child(self.main_container)

    def _build_ui(self, _: Gtk.Window):
        for app_data in self._installed_apps:
            self.content_container.append(
                AppRowWithCheckbox.build(
                    app_data=app_data,
                    checked=bool(app_data.executable in self._stored_apps)
                )
            )

        connect_button = Gtk.Button.new_with_label(label="Done")
        connect_button.set_name("split-tunneling-app-done-button")
        connect_button.add_css_class("primary")
        connect_button.set_halign(Gtk.Align.END)
        safe_signal_connect(
            connect_button, "clicked", self._on_done_button_clicked
        )
        self.main_container.append(connect_button)

    @GObject.Signal(name="app_selection_completed", arg_types=(object,))
    def app_selection_completed(self, selected_apps: list[AppData]):
        """
        Signal emitted after the user clicks on `Add` button.
        Since GObject can not parse `list[AppData]`, we need to always
        define it as an object.

        Args:
          selected_apps (list[AppData]): a list containing object to be split tunneled.
        """

    def _signal_updated_app_list(self, selected_apps: list[AppData]):
        self.emit("app_selection_completed", selected_apps)

    def _on_done_button_clicked(self, _: Gtk.Button):
        added_apps = []
        child = self.content_container.get_first_child()
        while child:
            if child.checked:
                added_apps.append(child.app_data)
            child = child.get_next_sibling()

        self._signal_updated_app_list(added_apps)
        self.close()

    def _get_first_app_(self) -> AppRowWithCheckbox:
        """Mainly for testing purposes and not for public API.

        Returns:
            AppRowWithCheckbox
        """
        return cast(AppRowWithCheckbox, self.content_container.get_first_child())

    def _click_on_done_button(self):
        """Mainly for testing purposes and not for public API.
        """
        last_child = self.main_container.get_last_child()
        if last_child:
            last_child.emit("clicked")
