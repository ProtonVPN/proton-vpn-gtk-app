from __future__ import annotations

import logging
from concurrent.futures import Future

from proton.vpn.core_api.session import LoginResult

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk  # noqa: E402

logger = logging.getLogger(__name__)


class View:
    """The V in the MVC pattern."""
    def __init__(self, controller):
        self._controller = controller
        self._login_window = LoginWindow(controller=self._controller)

    def run(self):
        self._login_window.show_all()
        return Gtk.main()


class LoginWindow(Gtk.ApplicationWindow):
    """Main window."""
    def __init__(self, controller):
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
        self._login_form.attach_next_to(
            self._username_entry, username_label, Gtk.PositionType.RIGHT, 2, 1)

        password_label = Gtk.Label("Password:")
        self._login_form.attach_next_to(
            password_label, username_label, Gtk.PositionType.BOTTOM, 1, 1)
        self._password_entry = Gtk.Entry()
        self._password_entry.set_width_chars(40)
        self._password_entry.set_visibility(False)
        self._login_form.attach_next_to(
            self._password_entry, self._username_entry,
            Gtk.PositionType.BOTTOM, 2, 1
        )
        self._login_button = Gtk.Button(label="Login")
        self._login_button.connect("clicked", self._on_login_button_clicked)
        self._login_form.attach_next_to(
            self._login_button, self._password_entry,
            Gtk.PositionType.BOTTOM, 1, 1
        )
        self._login_spinner = Gtk.Spinner()
        self._login_form.attach_next_to(
            self._login_spinner, self._login_button,
            Gtk.PositionType.BOTTOM, 1, 1
        )
        # 2FA form
        self._2fa_form = Gtk.Grid(row_spacing=10, column_spacing=10)
        self._stack.add_named(self._2fa_form, "2fa_form")

        twofa_code_label = Gtk.Label("2FA code:")
        self._2fa_form.attach(twofa_code_label, 0, 0, 1, 1)
        self._2fa_code_entry = Gtk.Entry()
        self._2fa_code_entry.set_width_chars(40)
        self._2fa_form.attach_next_to(
            self._2fa_code_entry, twofa_code_label,
            Gtk.PositionType.RIGHT, 2, 1)

        self._2fa_submission_button = Gtk.Button(label="Submit 2FA code")
        self._2fa_submission_button.connect(
            "clicked", self._on_2fa_submission_button_clicked)
        self._2fa_form.attach_next_to(
            self._2fa_submission_button, self._2fa_code_entry,
            Gtk.PositionType.BOTTOM, 1, 1)

        self._2fa_spinner = Gtk.Spinner()
        self._2fa_form.attach_next_to(
            self._2fa_spinner, self._2fa_submission_button,
            Gtk.PositionType.BOTTOM, 1, 1
        )
        # Main UI
        self._main = Gtk.Grid(row_spacing=10, column_spacing=10)
        self._main.set_column_homogeneous(True)
        self._main.set_orientation(Gtk.Orientation.VERTICAL)
        self._stack.add_named(self._main, "main")

        self._logout_button = Gtk.Button(label="Logout")
        self._logout_button.connect("clicked", self._on_logout_button_clicked)
        self._main.add(self._logout_button)
        self._connect_button = Gtk.Button(label="Connect")
        self._connect_button.connect(
            "clicked", self._on_connect_button_clicked)
        self._main.add(self._connect_button)
        self._disconnect_button = Gtk.Button(label="Disconnect")
        self._disconnect_button.connect(
            "clicked", self._on_disconnect_button_clicked)
        self._main.add(self._disconnect_button)
        self._main_spinner = Gtk.Spinner()
        self._main.add(self._main_spinner)

    def _on_login_button_clicked(self, _):
        self._login_spinner.start()
        future = self._controller.login(
            self._username_entry.get_text(), self._password_entry.get_text())
        future.add_done_callback(self._on_login_result)

    def _on_login_result(self, future: Future[LoginResult]):
        try:
            result = future.result()
        except Exception:
            logger.exception("Error during login.")
            return
        finally:
            self._login_spinner.stop()

        if result.success:
            logger.info("User logged in.")
            self._stack.set_visible_child(self._main)
        elif not result.authenticated:
            logger.error("Wrong password.")
        elif result.twofa_required:
            logger.info("Two factor auth required.")
            self._stack.set_visible_child(self._2fa_form)

    def _on_2fa_submission_button_clicked(self, _):
        self._2fa_spinner.start()
        future = self._controller.submit_2fa_code(
            self._2fa_code_entry.get_text()
        )
        future.add_done_callback(self._on_2fa_submission_result)

    def _on_2fa_submission_result(self, future: Future[LoginResult]):
        try:
            result = future.result()
        except Exception:
            logger.exception("Error during 2FA.")
            return
        finally:
            self._2fa_spinner.stop()

        if result.success:
            logger.info("User logged in.")
            self._stack.set_visible_child(self._main)
        elif result.twofa_required:
            logger.warning("Wrong 2FA code.")

    def _on_logout_button_clicked(self, _):
        logger.info("Disconnecting...")
        self._main_spinner.start()
        future = self._controller.logout()
        future.add_done_callback(self._on_logout_result)

    def _on_logout_result(self, future: Future):
        try:
            future.result()
        except Exception:
            logger.exception("Error during logout.")
            return
        finally:
            self._main_spinner.stop()

        logger.info("User logged out.")
        self._stack.set_visible_child(self._login_form)

    def _on_connect_button_clicked(self, _):
        logger.info("Connecting...")
        self._main_spinner.start()
        future = self._controller.connect()
        future.add_done_callback(self._on_connect_result)

    def _on_connect_result(self, future: Future):
        try:
            future.result()
        except Exception:
            logger.exception("Error during connect.")
            return
        finally:
            self._main_spinner.stop()
        logger.info("Connected.")

    def _on_disconnect_button_clicked(self, _):
        logger.info("Disconnecting...")
        self._main_spinner.start()
        future = self._controller.disconnect()
        future.add_done_callback(self._on_disconnect_result)

    def _on_disconnect_result(self, future: Future):
        try:
            future.result()
        except Exception:
            logger.exception("Error during disconnect.")
            return
        finally:
            self._main_spinner.stop()
        logger.info("Disconnected.")

    def _on_exit(self, *_):
        Gtk.main_quit()
