from __future__ import annotations

import logging
from concurrent.futures import Future

import gi
gi.require_version("Gtk", "3.0")  # noqa: GTK-specific requirement
from gi.repository import Gtk

from proton.vpn.core_api.session import LoginResult

logger = logging.getLogger(__name__)


class View:
    def __init__(self, controller: "Controller"):
        self._controller = controller
        self._login_window = LoginWindow(controller=self._controller)

    def run(self):
        self._login_window.show_all()
        return Gtk.main()


class LoginWindow(Gtk.ApplicationWindow):
    def __init__(self, controller: "Controller"):
        super().__init__(title="Proton VPN")

        self._controller = controller

        self._init_ui()

    def _init_ui(self):
        self.connect("destroy", self._on_exit)

        self.set_size_request(400, 150)

        self.set_border_width(10)

        self._stack = Gtk.Stack()
        self.add(self._stack)

        # Login form
        self._login_form = Gtk.Grid(row_spacing=10, column_spacing=10)
        self._stack.add_named(self._login_form, "login_form")

        username_label = Gtk.Label("Username:")
        self._login_form.attach(username_label, 0, 0, 1, 1)
        self._username_entry = Gtk.Entry()
        self._username_entry.set_width_chars(40)
        self._login_form.attach_next_to(self._username_entry, username_label, Gtk.PositionType.RIGHT, 2, 1)

        password_label = Gtk.Label("Password:")
        self._login_form.attach_next_to(password_label, username_label, Gtk.PositionType.BOTTOM, 1, 1)
        self._password_entry = Gtk.Entry()
        self._password_entry.set_width_chars(40)
        self._password_entry.set_visibility(False)
        self._login_form.attach_next_to(self._password_entry, self._username_entry, Gtk.PositionType.BOTTOM, 2, 1)

        self._login_button = Gtk.Button(label="Login")
        self._login_button.connect("clicked", self._on_login_button_clicked)
        self._login_form.attach_next_to(self._login_button, self._password_entry, Gtk.PositionType.BOTTOM, 1, 1)

        # 2FA form
        self._2fa_form = Gtk.Grid(row_spacing=10, column_spacing=10)
        self._stack.add_named(self._2fa_form, "2fa_form")

        twofa_code_label = Gtk.Label("2FA code:")
        self._2fa_form.attach(twofa_code_label, 0, 0, 1, 1)
        self._2fa_code_entry = Gtk.Entry()
        self._2fa_code_entry.set_width_chars(40)
        self._2fa_form.attach_next_to(self._2fa_code_entry, twofa_code_label, Gtk.PositionType.RIGHT, 2, 1)
        self._2fa_submission_button = Gtk.Button(label="Submit 2FA code")
        self._2fa_submission_button.connect("clicked", self._on_2fa_submission_button_clicked)
        self._2fa_form.attach_next_to(self._2fa_submission_button, self._2fa_code_entry, Gtk.PositionType.BOTTOM, 1, 1)

        # Main UI
        self._main = Gtk.Grid(row_spacing=10, column_spacing=10)
        self._main.set_column_homogeneous(True)
        self._main.set_orientation(Gtk.Orientation.VERTICAL)
        self._stack.add_named(self._main, "main")

        self._logout_button = Gtk.Button(label="Logout")
        self._logout_button.connect("clicked", self._on_logout_button_clicked)
        self._main.add(self._logout_button)
        self._connect_button = Gtk.Button(label="Connect")
        self._connect_button.connect("clicked", self._on_connect_button_clicked)
        self._main.add(self._connect_button)
        self._disconnect_button = Gtk.Button(label="Disconnect")
        self._disconnect_button.connect("clicked", self._on_disconnect_button_clicked)
        self._main.add(self._disconnect_button)

    def _on_login_button_clicked(self, _):
        future = self._controller.login(self._username_entry.get_text(), self._password_entry.get_text())
        future.add_done_callback(self._on_login_result)

    def _on_login_result(self, future: Future[LoginResult]):
        try:
            result = future.result()
        except Exception:
            logger.exception("Error during login.")
            return

        if result.success:
            logger.info("User logged in.")
            self._stack.set_visible_child(self._main)
        elif not result.authenticated:
            logger.error("Wrong password.")
        elif result.twofa_required:
            logger.info("Two factor auth required.")
            self._stack.set_visible_child(self._2fa_form)

    def _on_2fa_submission_button_clicked(self, _):
        future = self._controller.submit_2fa_code(self._2fa_code_entry.get_text())
        future.add_done_callback(self._on_2fa_submission_result)

    def _on_2fa_submission_result(self, future: Future[LoginResult]):
        try:
            result = future.result()
        except Exception:
            logger.exception("Error during 2FA.")
            return

        if result.success:
            logger.info("User logged in.")
            self._stack.set_visible_child(self._main)
        elif result.twofa_required:
            logger.warning("Wrong 2FA code.")

    def _on_logout_button_clicked(self, _):
        future = self._controller.logout()
        future.add_done_callback(self._on_logout_result)

    def _on_logout_result(self, future: Future):
        try:
            future.result()
        except Exception:
            logger.exception("Error during logout.")
            return

        logger.info("User logged out.")
        self._stack.set_visible_child(self._login_form)

    def _on_connect_button_clicked(self, _):
        logger.info("Connecting...")
        future = self._controller.connect()
        future.add_done_callback(self._on_connect_result)

    def _on_connect_result(self, future: Future):
        try:
            future.result()
        except Exception:
            logger.exception("Error during connect.")
            return
        logger.info("Connected.")

    def _on_disconnect_button_clicked(self, _):
        logger.info("Disconnecting...")
        future = self._controller.disconnect()
        future.add_done_callback(self._on_disconnect_result)

    def _on_disconnect_result(self, future: Future):
        try:
            future.result()
        except Exception:
            logger.exception("Error during disconnect.")
            return
        logger.info("Disconnected.")

    def _on_exit(self, *_):
        Gtk.main_quit()
