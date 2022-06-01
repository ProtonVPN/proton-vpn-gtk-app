from __future__ import annotations

from concurrent.futures import Future

import gi
gi.require_version("Gtk", "3.0")  # noqa: GTK-specific requirement
from gi.repository import Gtk

from proton.vpn.core_api.session import LoginResult


class View:
    def __init__(self, controller: "Controller"):
        self._controller = controller
        self._login_window = LoginWindow(controller=self._controller)

    def run(self):
        self._login_window.show_all()
        return Gtk.main()


class LoginWindow(Gtk.ApplicationWindow):
    def __init__(self, controller: "Controller"):
        super().__init__(title="Proton VPN - Login")

        self._controller = controller

        self._init_ui()

    def _init_ui(self):
        self.connect("destroy", self._on_exit)

        self.set_size_request(400, 150)

        self.set_border_width(10)

        self._stack = Gtk.Stack()
        self.add(self._stack)

        # Setting up the grid in which the elements are to be positioned
        self._login_form = Gtk.Grid()
        self._login_form.set_column_homogeneous(True)
        # self._login_form.set_row_homogeneous(True)
        self._login_form.set_row_spacing(10)
        self._stack.add_named(self._login_form, "login_form")

        self._username_entry = Gtk.Entry()
        # self._username_entry.
        self._login_form.attach(self._username_entry, 0, 0, 1, 1)

        self._password_entry = Gtk.Entry()
        self._password_entry.set_visibility(False)
        self._login_form.attach_next_to(self._password_entry, self._username_entry, Gtk.PositionType.BOTTOM, 1, 1)

        # Add login button
        self._login_button = Gtk.Button(label="Login")
        self._login_button.connect("clicked", self._on_login_button_clicked)
        self._login_form.attach_next_to(self._login_button, self._password_entry, Gtk.PositionType.BOTTOM, 1, 1)

        self._2fa_form = Gtk.Grid()
        self._2fa_form.set_column_homogeneous(True)
        # self._2fa_form.set_row_homogeneous(True)
        self._2fa_form.set_row_spacing(10)
        self._stack.add_named(self._2fa_form, "2fa_form")

        self._2fa_code_entry = Gtk.Entry()
        self._2fa_form.attach(self._2fa_code_entry, 0, 0, 1, 1)

        # Add 2FA code submission button
        self._2fa_submission_button = Gtk.Button(label="Submit 2FA code")
        self._2fa_submission_button.connect("clicked", self._on_2fa_submission_button_clicked)
        self._2fa_form.attach_next_to(self._2fa_submission_button, self._2fa_code_entry, Gtk.PositionType.BOTTOM, 1, 1)

        self._main = Gtk.VBox()
        self._stack.add_named(self._main, "main")

        logged_in_label = Gtk.Label(f"Logged in.")
        self._main.add(logged_in_label)


    def _on_login_button_clicked(self, _):
        future = self._controller.submit_login_credentials(
            self._username_entry.get_text(), self._password_entry.get_text()
        )
        future.add_done_callback(self._on_login_result)

    def _on_login_result(self, future: Future[LoginResult]):
        result = future.result()
        if result.success:
            print("User logged in.")
            self._stack.set_visible_child(self._main)
        elif not result.authenticated:
            print("Wrong password.")
        elif result.twofa_required:
            print("Two factor auth required.")
            self._stack.set_visible_child(self._2fa_form)

    def _on_2fa_submission_button_clicked(self, _):
        future = self._controller.submit_2fa_code(self._2fa_code_entry.get_text())
        future.add_done_callback(self._on_2fa_submission_result)

    def _on_2fa_submission_result(self, future: Future[LoginResult]):
        result = future.result()
        if result.success:
            print("User logged in.")
            self._stack.set_visible_child(self._main)
        elif result.twofa_required:
            print("Wrong 2FA code")

    def _on_exit(self, *_):
        Gtk.main_quit()
