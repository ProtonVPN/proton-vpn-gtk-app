"""
This module defines the headerbar widget
that is present at the top of the window.
"""
from typing import TYPE_CHECKING
from concurrent.futures import Future

from gi.repository import Gio, GLib, GObject
from proton.vpn.app.gtk import Gtk

from proton.vpn.app.gtk.widgets.report import BugReportWidget
from proton.vpn.app.gtk.widgets.about import AboutWidget
from proton.vpn.app.gtk.widgets.disconnect import DisconnectDialog
from proton.vpn.app.gtk.controller import Controller

from proton.session.exceptions import ProtonAPINotReachable
from proton.vpn import logging

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from proton.vpn.app.gtk.app import MainWindow


class HeaderBarWidget(Gtk.HeaderBar):
    """Headerbar widget.
    Allows to customize the headerbar (also known as the title bar),
    by adding custom buttons, icons and text.
    """
    UNABLE_TO_LOGOUT_TITLE = "Unable to Logout"
    UNABLE_TO_LOGOUT_MESSAGE = "Please ensure you have internet access."
    DISCONNECT_ON_LOGOUT_MESSAGE = "Logging out of the application will disconnect the active"\
        " VPN connection.\n\nDo you want to continue?"
    DISCONNECT_ON_QUIT_MESSAGE = "Quitting the application will disconnect the active" \
                                 " VPN connection.\n\nDo you want to continue?"

    def __init__(self, controller: Controller, main_window: "MainWindow"):
        super().__init__()

        self.set_decoration_layout("menu:minimize,close")
        self.set_title("Proton VPN")
        self.set_show_close_button(True)

        self._controller = controller
        self._main_window = main_window
        self._menu_button_widget = Gtk.MenuButton()
        self._menu_widget = MenuWidget()
        self._menu_button_widget.set_menu_model(self._menu_widget)
        self._setup_actions()
        self.pack_start(self._menu_button_widget)

    @property
    def logout_enabled(self) -> bool:
        """Returns if logout button is enabled or disabled."""
        return self._menu_widget.logout_action.get_enabled()

    @logout_enabled.setter
    def logout_enabled(self, newvalue: bool):
        """Set the logout button to either be enabled or disabled."""
        self._menu_widget.logout_action.set_enabled(newvalue)

    @GObject.Signal
    def user_logged_out(self):
        """Signal emitted after a successful logout."""

    def _setup_actions(self):
        # Add actions to Gtk.ApplicationWindow
        self._main_window.add_action(self._menu_widget.bug_report_action)
        self._main_window.add_action(self._menu_widget.about_action)
        self._main_window.add_action(self._menu_widget.logout_action)
        self._main_window.add_action(self._menu_widget.quit_action)

        # Connect actions to callbacks
        self._menu_widget.bug_report_action.connect(
            "activate", self._on_report_an_issue_clicked
        )
        self._menu_widget.about_action.connect(
            "activate", self._on_about_clicked
        )
        self._menu_widget.logout_action.connect(
            "activate", self._on_logout_clicked
        )
        self._menu_widget.quit_action.connect(
            "activate", self._on_quit_clicked
        )

    def _on_report_an_issue_clicked(self, *_):
        bug_dialog = BugReportWidget(self._controller)
        bug_dialog.set_transient_for(self._main_window)
        # run() blocks the main loop, and only exist once the `::response` signal
        # is emitted.
        bug_dialog.run()
        bug_dialog.destroy()

    def _on_about_clicked(self, *_):
        about_dialog = AboutWidget()
        # run() blocks the main loop, and only exist once the `::response` signal
        # is emitted.
        about_dialog.run()
        about_dialog.destroy()

    def _on_logout_clicked(self, *_):
        logger.info("Logout button clicked", category="ui", subcategory="logout", event="click")
        self.logout_enabled = False
        confirm_logout = True

        if self._controller.is_connection_active:
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
            self._request_logout()

    def _on_quit_clicked(self, *_):
        confirm_quit = True

        if self._controller.is_connection_active:
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
            self._main_window.destroy()

    def _request_logout(self):
        future = self._controller.logout()
        future.add_done_callback(
            lambda future: GLib.idle_add(self._on_logout_result, future)
        )

    def _on_logout_result(self, future: Future):
        """Callback when attempting to logout.
        Mainly used to emit if a sucessful logout has happened, or if a
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
            self.logout_enabled = True
            self._main_window.main_widget.show_error_message(
                self.UNABLE_TO_LOGOUT_MESSAGE,
                True, self.UNABLE_TO_LOGOUT_TITLE
            )

    def bug_report_button_click(self):
        """Button to simulate bug report click.
        This method was made available mainly for testing purposes.
        """
        self._on_report_an_issue_clicked(self._menu_widget.bug_report_action)

    def about_button_click(self):
        """Button to simulate about click.
        This method was made available mainly for testing purposes.
        """
        self._on_about_clicked(self._menu_widget.about_action)

    def logout_button_click(self):
        """Button to simulate quit click.
        This method was made available mainly for testing purposes.
        """
        self._on_logout_clicked(self._menu_widget.logout_action)

    def quit_button_click(self):
        """Button to simulate logout click.
        This method was made available mainly for testing purposes.
        """
        self._on_quit_clicked(self._menu_widget.quit_action)


class MenuWidget(Gio.Menu):
    """Custom menu widget that is displayed in the headerbar."""
    def __init__(self):
        super().__init__()
        self.bug_report_action = Gio.SimpleAction.new("report", None)
        self.about_action = Gio.SimpleAction.new("about", None)
        self.logout_action = Gio.SimpleAction.new("logout", None)
        self.quit_action = Gio.SimpleAction.new("quit", None)

        self.append_item(Gio.MenuItem.new("Report an Issue", "win.report"))
        self.append_item(Gio.MenuItem.new("About", "win.about"))
        self.append_item(Gio.MenuItem.new("Logout", "win.logout"))
        self.append_item(Gio.MenuItem.new("Exit", "win.quit"))
