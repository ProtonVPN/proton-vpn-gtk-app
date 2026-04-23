"""
This module defines the main App class.


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

from typing import Any, Optional
from gi.repository import GObject, Gtk, Gdk, GLib

from proton.vpn import logging

from proton.vpn.app.gtk.controller import Controller
from proton.vpn.app.gtk.widgets.main.main_window import MainWindow
from proton.vpn.app.gtk.assets.style import STYLE_PATH
from proton.vpn.app.gtk.util import APPLICATION_ID, log_proton_package_versions
from proton.vpn.app.gtk.widgets.main.tray_indicator import TrayIndicator, TrayIndicatorNotSupported

logger = logging.getLogger(__name__)


class App(Gtk.Application):
    """
    Proton VPN GTK application.

    It inherits a set of common app functionality from Gtk.Application:
    https://docs.gtk.org/gtk3/class.Application.html.

    For example:
     - It guarantees that only one instance of the application is
       allowed (new app instances exit immediately if there is already
       an instance running).
     - It manages the windows associated to the application. The application
       exits automatically when the last one is closed.
     - It allows desktop shell integration by exporting actions and menus.
    """
    def __init__(
            self,
            controller: Controller
    ):
        super().__init__(application_id=APPLICATION_ID)
        logger.info(f"{self=}", category="APP", event="PROCESS_START")
        log_proton_package_versions()
        self._controller = controller
        self.window: Optional[MainWindow] = None
        self._tray_indicator = None
        self._signal_connect_queue: list[Any] = []
        self._start_minimized_from_cli = False
        self.add_options()

    def do_startup(self):  # pylint: disable=arguments-differ
        """Default GTK method.

        Runs at application startup, to load
        any necessary UI elements.
        """
        Gtk.Application.do_startup(self)
        css_provider = Gtk.CssProvider()
        css_provider.load_from_path(str(STYLE_PATH / "main.css"))

        display = Gdk.Display.get_default()
        Gtk.StyleContext.add_provider_for_display(
            display,
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def do_activate(self):  # pylint: disable=W0221
        """
        Method called by Gtk.Application when the default first window should
        be shown to the user.
        """
        if not self.window:
            self.window = MainWindow(self, self._controller)
            # Windows are associated with the application like this.
            # When the last one is closed, the application shuts down.
            self.add_window(self.window)
            # The behaviour of the button to close the window is configured
            # depending on whether the tray indicator is shown or not.
            self.window.configure_close_button_behaviour(
                tray_indicator_enabled=(self.tray_indicator is not None)
            )
            self.window.set_visible(True)

        self.window.present()
        self.emit("app-ready")

    def do_handle_local_options(self, options: GLib.VariantDict):  # noqa: E501 pylint: disable=arguments-differ
        """
        Handles the options defined in add_options
        Returns:
            Any negative number: Start as usual
            Zero: Stop without error
            Any positive number: Stop with the number as error code
        """
        if options.contains("version"):
            print(self._controller.app_version)
            return 0

        if options.contains("start-minimized"):
            self._start_minimized_from_cli = True

        return -1

    @property
    def error_dialog(self) -> Gtk.MessageDialog:
        """
        Gives access to currently opened error message dialogs. This method
        was made available for testing purposes.
        """
        return self.window.main_widget.notifications.error_dialog

    @GObject.Signal(name="app-ready")
    def app_ready(self):
        """Signal emitted when the app is ready for interaction."""
        if self._start_app_minimized and self.tray_indicator:
            self.window.set_visible(False)

    @property
    def _start_app_minimized(self) -> bool:
        return self._start_minimized_from_cli \
            or self._controller.get_app_configuration().start_app_minimized

    def add_options(self):
        """Adds the --start-minimized and --version command line options"""
        self.add_main_option(
            "start-minimized",
            0,
            GLib.OptionFlags(0),
            GLib.OptionArg.NONE,
            "Start minimized in the system tray"
        )

        self.add_main_option(
            "version",
            ord('v'),
            GLib.OptionFlags(0),
            GLib.OptionArg.NONE,
            "Display the application's version"
        )

    @property
    def tray_indicator(self):
        """Gives access to the tray indicator if it's installed and enabled."""
        if self._tray_indicator:
            return self._tray_indicator

        try:
            tray_indicator = TrayIndicator(self._controller)
            tray_indicator.setup(self.window)
        except TrayIndicatorNotSupported as excp:
            logger.warning(str(excp))
        else:
            self._tray_indicator = tray_indicator

        return self._tray_indicator
