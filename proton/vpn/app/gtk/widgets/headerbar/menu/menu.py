"""
This module defines the menu that shown in the header bar.


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
from typing import TYPE_CHECKING
from concurrent.futures import Future

from gi.repository import Gio, GLib, GObject
from proton.vpn.app.gtk import Gtk

from proton.vpn.app.gtk.widgets.headerbar.menu.bug_report_dialog import BugReportDialog
from proton.vpn.app.gtk.widgets.headerbar.menu.about_dialog import AboutDialog
from proton.vpn.app.gtk.widgets.headerbar.menu.disconnect_dialog import DisconnectDialog
from proton.vpn.app.gtk.controller import Controller
from proton.vpn.app.gtk.widgets.main.loading_widget import LoadingWidget
from proton.vpn.app.gtk.widgets.headerbar.menu.settings import SettingsWindow

from proton.session.exceptions import ProtonAPINotReachable
from proton.vpn import logging

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from proton.vpn.app.gtk.app import MainWindow


class Menu(Gio.Menu):  # pylint: disable=too-many-instance-attributes
    """App menu shown in the header bar."""

    LOGOUT_LOADING_MESSAGE = "Logging out..."
    UNABLE_TO_LOGOUT_MESSAGE = "Unable to logout, please ensure you have internet access."
    DISCONNECT_ON_LOGOUT_MESSAGE = "Logging out of the application will cancel the current" \
                                   " VPN connection.\n\nDo you want to continue?"
    DISCONNECT_ON_QUIT_MESSAGE = "Quitting the application will cancel the current" \
                                 " VPN connection.\n\nDo you want to continue?"

    def __init__(
        self, controller: Controller,
        main_window: "MainWindow", loading_widget: LoadingWidget
    ):
        super().__init__()
        self._main_window = main_window
        self._controller = controller
        self._loading_widget = loading_widget

        self.settings_action = Gio.SimpleAction.new("settings", None)
        self.bug_report_action = Gio.SimpleAction.new("report", None)
        self.about_action = Gio.SimpleAction.new("about", None)
        self.logout_action = Gio.SimpleAction.new("logout", None)
        self.quit_action = Gio.SimpleAction.new("quit", None)

        self.append_item(Gio.MenuItem.new("Report an issue", "win.report"))
        self.append_item(Gio.MenuItem.new("Settings", "win.settings"))
        self.append_item(Gio.MenuItem.new("About", "win.about"))
        self.append_item(Gio.MenuItem.new("Logout", "win.logout"))
        self.append_item(Gio.MenuItem.new("Quit", "win.quit"))

        self._setup_actions()

    @property
    def logout_enabled(self) -> bool:
        """Returns if logout button is enabled or disabled."""
        return self.logout_action.get_enabled()

    @logout_enabled.setter
    def logout_enabled(self, newvalue: bool):
        """Set the logout button to either be enabled or disabled."""
        self.logout_action.set_enabled(newvalue)

    @GObject.Signal
    def user_logged_out(self):
        """Signal emitted after a successful logout."""

    def _setup_actions(self):
        # Add actions to Gtk.ApplicationWindow
        self._main_window.add_action(self.settings_action)
        self._main_window.add_action(self.bug_report_action)
        self._main_window.add_action(self.about_action)
        self._main_window.add_action(self.logout_action)
        self._main_window.add_action(self.quit_action)

        # Connect actions to callbacks
        self.settings_action.connect(
            "activate", self._on_settings_clicked
        )
        self.bug_report_action.connect(
            "activate", self._on_report_an_issue_clicked
        )
        self.about_action.connect(
            "activate", self._on_about_clicked
        )
        self.logout_action.connect(
            "activate", self._on_logout_clicked
        )
        self.quit_action.connect(
            "activate", self._on_quit_clicked
        )

    def _on_settings_clicked(self,  *_):
        settings_window = SettingsWindow(self._controller)
        settings_window.present()

    def _on_report_an_issue_clicked(self, *_):
        bug_dialog = BugReportDialog(self._controller, self._main_window)
        bug_dialog.set_transient_for(self._main_window)
        # run() blocks the main loop, and only exist once the `::response` signal
        # is emitted.
        bug_dialog.run()
        bug_dialog.destroy()

    def _on_about_clicked(self, *_):
        about_dialog = AboutDialog()
        # run() blocks the main loop, and only exist once the `::response` signal
        # is emitted.
        about_dialog.run()
        about_dialog.destroy()

    def _on_logout_clicked(self, *_):
        logger.info("Logout button clicked", category="ui", subcategory="logout", event="click")
        self.logout_enabled = False
        confirm_logout = True

        if not self._controller.is_connection_disconnected:
            logout_dialog = DisconnectDialog(
                message=self.DISCONNECT_ON_LOGOUT_MESSAGE
            )
            logout_dialog.set_transient_for(self._main_window)
            # run() blocks the main loop, and only exist once the `::response` signal
            # is emitted.
            response = Gtk.ResponseType(logout_dialog.run())
            logout_dialog.destroy()

            confirm_logout = response == Gtk.ResponseType.YES
            self.logout_enabled = response == Gtk.ResponseType.NO

        if confirm_logout:
            logger.info("Yes", category="ui", subcategory="dialog", event="logout")
            self._loading_widget.show(self.LOGOUT_LOADING_MESSAGE)
            self._request_logout()

    def _on_quit_clicked(self, *_):
        confirm_quit = True

        if not self._controller.is_connection_disconnected:
            quit_dialog = DisconnectDialog(
                message=self.DISCONNECT_ON_QUIT_MESSAGE
            )
            quit_dialog.set_transient_for(self._main_window)
            # run() blocks the main loop, and only exist once the `::response` signal
            # is emitted.
            response = Gtk.ResponseType(quit_dialog.run())
            quit_dialog.destroy()

            confirm_quit = response == Gtk.ResponseType.YES

        if confirm_quit:
            logger.info("Yes", category="ui", subcategory="dialog", event="quit")
            self._main_window.quit()

    def _request_logout(self):
        future = self._controller.logout()
        future.add_done_callback(
            lambda future: GLib.idle_add(self._on_logout_result, future)
        )

    def _on_logout_result(self, future: Future):
        """Callback when attempting to log out.
        Mainly used to emit if a successful logout has happened, or if a
            connection is found at logout, to display the dialog to the user.
        """
        try:
            future.result()
            logger.info(
                "Successful logout",
                category="app", subcategory="logout", event="success"
            )
            self.emit("user-logged-out")
        except ProtonAPINotReachable as e:  # pylint: disable=invalid-name
            logger.info(
                getattr(e, 'message', repr(e)),
                category="app", subcategory="logout", event="fail"
            )
            self._main_window.main_widget.notifications.show_error_message(
                self.UNABLE_TO_LOGOUT_MESSAGE
            )
        finally:
            self.logout_enabled = True
            self._loading_widget.hide()

    def bug_report_button_click(self):
        """Clicks the bug report menu entry."""
        self._on_report_an_issue_clicked(self.bug_report_action)

    def about_button_click(self):
        """Clicks the about menu entry."""
        self._on_about_clicked(self.about_action)

    def logout_button_click(self):
        """Clicks the logout menu entry."""
        self._on_logout_clicked(self.logout_action)

    def quit_button_click(self):
        """Clicks the quit menu entry."""
        self._on_quit_clicked(self.quit_action)
