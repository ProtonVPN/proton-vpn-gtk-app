import logging
from concurrent.futures import Future

from proton.vpn.core_api.session import LoginResult

from gi.repository import GObject
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk  # noqa: E402

logger = logging.getLogger(__name__)


class LoginWidget(Gtk.Bin):
    """Widget used to authenticate the user."""
    def __init__(self, controller):
        super().__init__()
        self._controller = controller

        self._stack = Gtk.Stack()
        self.add(self._stack)

        self._login_form = Gtk.Grid(row_spacing=10, column_spacing=10)
        self._stack.add_named(self._login_form, "login_form")
        self._2fa_form = Gtk.Grid(row_spacing=10, column_spacing=10)
        self._stack.add_named(self._2fa_form, "2fa_form")

        self._login_form.set_column_homogeneous(True)
        self._username_entry = Gtk.Entry()
        self._username_entry.set_placeholder_text("Username")
        self._login_form.add(self._username_entry)

        self._password_entry = Gtk.Entry()
        self._password_entry.set_placeholder_text("Password")
        self._password_entry.set_visibility(False)
        self._login_form.attach_next_to(
            self._password_entry, self._username_entry,
            Gtk.PositionType.BOTTOM, 1, 1)

        self._login_button = Gtk.Button(label="Login")
        self._login_button.connect("clicked", self._on_login_button_clicked)
        self._login_form.attach_next_to(
            self._login_button, self._password_entry,
            Gtk.PositionType.BOTTOM, 1, 1
        )
        # The focus is set on the button because otherwise is set on the
        # username entry and the placeholder is not shown.
        self._login_button.grab_focus()
        # Pressing enter on the password entry triggers the clicked event
        # on the login button
        self._password_entry.connect(
            "activate", lambda _: self._login_button.clicked())

        self._login_spinner = Gtk.Spinner()
        self._login_form.attach_next_to(
            self._login_spinner, self._login_button,
            Gtk.PositionType.BOTTOM, 1, 1
        )

        self._2fa_form.set_column_homogeneous(True)
        self._2fa_code_entry = Gtk.Entry()
        self._2fa_code_entry.set_placeholder_text("Insert your 2FA code here")
        self._2fa_form.add(self._2fa_code_entry)

        self._2fa_submission_button = Gtk.Button(label="Submit 2FA code")
        self._2fa_submission_button.connect(
            "clicked", self._on_2fa_submission_button_clicked)
        self._2fa_form.attach_next_to(
            self._2fa_submission_button, self._2fa_code_entry,
            Gtk.PositionType.BOTTOM, 1, 1)
        # The focus is set on the button because otherwise is set on the
        # 2FA code entry and the placeholder is not shown.
        self._2fa_submission_button.grab_focus()
        # Pressing enter on the password entry triggers the clicked event
        # on the login button
        self._2fa_code_entry.connect(
            "activate", lambda _: self._2fa_submission_button.clicked())

        self._2fa_spinner = Gtk.Spinner()
        self._2fa_form.attach_next_to(
            self._2fa_spinner, self._2fa_submission_button,
            Gtk.PositionType.BOTTOM, 1, 1
        )

    @GObject.Signal(name="user-logged-in")
    def user_logged_in(self):
        pass

    def reset(self):
        self._username_entry.set_text("")
        self._password_entry.set_text("")
        self._2fa_code_entry.set_text("")
        self._login_button.grab_focus()
        self._stack.set_visible_child(self._login_form)

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
            self.emit("user-logged-in")
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
            self.emit("user-logged-in")
        elif result.twofa_required:
            logger.warning("Wrong 2FA code.")
