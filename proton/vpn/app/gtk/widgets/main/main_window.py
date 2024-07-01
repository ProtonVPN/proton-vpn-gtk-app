"""
This module defines the main application window.


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
from pathlib import Path

from gi.repository import Gdk, Gtk

from proton.vpn.app.gtk.assets import icons
from proton.vpn.app.gtk.controller import Controller
from proton.vpn.app.gtk.widgets.main.main_widget import MainWidget
from proton.vpn.app.gtk.widgets.headerbar.headerbar import HeaderBar
from proton.vpn.app.gtk.widgets.main.notification_bar import NotificationBar
from proton.vpn.app.gtk.widgets.main.notifications import Notifications
from proton.vpn.app.gtk.widgets.main.loading_widget import OverlayWidget


class MainWindow(Gtk.ApplicationWindow):
    """Main window."""

    WIDTH = 400
    HEIGTH = 600

    # pylint: disable=too-many-arguments
    def __init__(
            self, application: Gtk.Application,
            controller: Controller,
            notifications: Notifications = None,
            header_bar: HeaderBar = None,
            main_widget: MainWidget = None,
            overlay_widget: OverlayWidget = None
    ):
        super().__init__(application=application)
        self._application = application
        self.get_settings().props.gtk_application_prefer_dark_theme = True
        self._controller = controller
        self._close_window_handler_id = None

        self._configure_window()

        self._overlay_widget = overlay_widget or OverlayWidget()

        notifications = notifications or Notifications(
            main_window=self, notification_bar=NotificationBar()
        )

        self.header_bar = header_bar or HeaderBar(
            controller=controller,
            main_window=self,
            overlay_widget=self._overlay_widget
        )
        self.set_titlebar(self.header_bar)

        self.main_widget = main_widget or MainWidget(
            controller=controller,
            main_window=self,
            notifications=notifications,
            overlay_widget=self._overlay_widget
        )
        self.add(self.main_widget)

    @property
    def application(self) -> Gtk.Application:
        """Returns Gtk.Application object which contains references to windows,
        tray indicator and other settings."""
        return self._application

    def add_keyboard_shortcut(self, target_widget: Gtk.Widget, target_signal: str, shortcut: str):
        """
        Adds a keyboard shortcut so that when pressed it causes the target signal
        to be triggered on the target widget.

        :param target_widget: The widget the keyboard shortcut will trigger the signal on.
        :param target_signal: The signal the keyboard shortcut will trigger on the target widget.
        :param shortcut: The keyboard shortcut should be a string parseable with
        Gtk.parse_accelerator:
        https://lazka.github.io/pgi-docs/#Gtk-3.0/functions.html#Gtk.accelerator_parse
        """
        key, modifier = Gtk.accelerator_parse(shortcut)
        target_widget.add_accelerator(
            target_signal, self._accelerators_group,
            key, modifier, Gtk.AccelFlags.VISIBLE
        )

    def _configure_window(self):
        """
        Handle delete-event, set window resize restrictions...
        """

        # The accelerator group is used to then add keyboard shortcuts.
        self.set_name("main-window")
        self._accelerators_group = Gtk.AccelGroup()
        self.add_accel_group(self._accelerators_group)

        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_icon(
            icons.get(Path("proton-vpn-sign.svg"), width=128, height=128)
        )

        # The window should be able to be resized on the vertical axis but not
        # on the horizontal axis.
        self.set_size_request(MainWindow.WIDTH, MainWindow.HEIGTH)
        geometry = Gdk.Geometry()
        geometry.min_width = 0
        geometry.max_width = MainWindow.WIDTH
        geometry.min_height = 0
        geometry.max_height = 99999
        self.set_geometry_hints(
            self,
            geometry,
            (Gdk.WindowHints.MIN_SIZE | Gdk.WindowHints.MAX_SIZE)
        )

        self.set_border_width(0)

    def configure_close_button_behaviour(self, tray_indicator_enabled: bool):
        """Configures the behaviour of the button to close the window
        (the x button), depending on if the tray indicator is used or not."""
        if tray_indicator_enabled:
            self._close_window_handler_id = self.configure_close_button_to_hide_window()
        else:
            self._close_window_handler_id = self.configure_close_button_to_trigger_quit_menu_entry()

    def configure_close_button_to_hide_window(self):
        """Configures the x (close window) button so that when clicked,
        the window is hidden instead closed."""
        def on_close_button_clicked_then_hide_window(*_) -> bool:
            """
            Instead of letting the window x button close the app, therefore
            quitting the app, the action is delegated to the Exit entry in
            the menu bar widget.
            """
            self.hide()

            # Returning True when handling the delete-event stops other handlers
            # from being invoked for this event, therefore preventing the default
            # behaviour:
            # https://docs.gtk.org/gtk3/signal.Widget.delete-event.html
            return True

        # Handle the event emitted when the user tries to close the window.
        return self.connect(
            "delete-event",
            on_close_button_clicked_then_hide_window
        )

    def quit(self):
        """Closes the main window, which quits the app."""
        if self._close_window_handler_id:
            self.disconnect(self._close_window_handler_id)

        self.close()

    def configure_close_button_to_trigger_quit_menu_entry(self):
        """Configures the x (close window) button so that when clicked,
        the Exit menu entry is triggered instead."""
        def on_close_button_clicked_then_click_quit_menu_entry(*_) -> bool:
            """
            Instead of letting the x button close the app, therefore
            quitting the app, the action is delegated to the Exit entry in
            the menu bar widget, which may request confirmation to the user.
            """
            self.header_bar.menu.quit_button_click()

            # Returning True when handling the delete-event stops other handlers
            # from being invoked for this event, therefore preventing the default
            # behaviour:
            # https://docs.gtk.org/gtk3/signal.Widget.delete-event.html
            return True

        # Handle the event emitted when the user tries to close the window.
        return self.connect(
            "delete-event",
            on_close_button_clicked_then_click_quit_menu_entry
        )
