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


from gi.repository import Gtk, GObject


from proton.vpn.app.gtk.controller import Controller
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
        gtk: Gtk = Gtk
    ):  # pylint: disable=too-many-arguments
        super().__init__(type=Gtk.WindowType.TOPLEVEL)
        self.set_modal(True)
        self.set_title(title)
        self.set_default_size(600, 500)
        self.set_position(Gtk.WindowPosition.CENTER_ON_PARENT)
        self.set_name("split-tunneling-app-selection-window")

        self.gtk = gtk
        self._controller = controller
        self._stored_apps = stored_apps
        self._installed_apps = installed_apps

        # Can't use self.container as that seems to be a non-writable property,
        # probably reserved by Gtk.
        self.main_container = Gtk.Box.new(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.content_container = Gtk.Box.new(orientation=Gtk.Orientation.VERTICAL, spacing=10)

        self._create_elastic_window()

        self.connect("realize", self._build_ui)

    def _create_elastic_window(self):
        """This allows for the content to be always centered and expand or contract
        based on window size.

        The reason we use two containers is mainly due to the notification bar, as this
        way the notification will span across the entire window while only the
        settings will be centered.
        """
        viewport = Gtk.Viewport.new(None, None)
        viewport.get_style_context().add_class("viewport-frame")
        viewport.add(self.content_container)

        scrolled_window = Gtk.ScrolledWindow.new()
        scrolled_window.set_propagate_natural_height(True)
        scrolled_window.set_min_content_height(200)
        scrolled_window.set_min_content_width(400)
        scrolled_window.add(viewport)

        self.main_container.pack_start(scrolled_window, False, False, 0)

        self.add(self.main_container)

    def _build_ui(self, _: Gtk.Window):
        for app_data in self._installed_apps:

            self.content_container.add(
                AppRowWithCheckbox.build(
                    app_data=app_data,
                    checked=bool(app_data.executable in self._stored_apps)
                )
            )

        connect_button = Gtk.Button.new_with_label(label="Done")
        connect_button.set_name("split-tunneling-app-done-button")
        connect_button.get_style_context().add_class("primary")
        connect_button.set_halign(Gtk.Align.END)
        connect_button.connect(
            "clicked", self._on_done_button_clicked
        )
        self.main_container.pack_end(connect_button, False, False, 0)

        self.show_all()

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
        for child in self.content_container.get_children():
            if not child.checked:
                continue

            added_apps.append(child.app_data)

        self._signal_updated_app_list(added_apps)
        self.close()

    def _get_first_app_(self) -> AppRowWithCheckbox:
        """Mainly for testing purposes and not for public API.

        Returns:
            AppRowWithCheckbox
        """
        return self.content_container.get_children()[0]

    def _click_on_done_button(self):
        """Mainly for testing purposes and not for public API.
        """
        self.main_container.get_children()[-1].clicked()
