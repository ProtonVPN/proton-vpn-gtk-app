import logging
from concurrent.futures import Future

from gi.repository import GObject

from proton.session.exceptions import ProtonError
from proton.vpn.core_api.session import LoginResult

from proton.vpn.app.gtk.controller import Controller
from proton.vpn.app.gtk import Gtk


logger = logging.getLogger(__name__)


class LoginWidget(Gtk.Bin):
    """Widget used to authenticate the user."""

    def __init__(self, controller: Controller):
        super().__init__()
        self._controller = controller
        self._active_form = None

        self._grid = Gtk.Grid()
        self._grid.set_column_homogeneous(True)
        self.add(self._grid)

        self._error = Gtk.Label(label="")
        self._error.set_margin_bottom(10)
        self._error.set_font_options()
        self._error.set_visible(False)

        self._grid.add(self._error)
        self._stack = Gtk.Stack()
        self._grid.attach_next_to(
            self._stack, self._error,
            Gtk.PositionType.BOTTOM, 1, 1
        )

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
        # Pressing enter on the password entry triggers the clicked event
        # on the login button.
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
        # Pressing enter on the password entry triggers the clicked event
        # on the login button.
        self._2fa_code_entry.connect(
            "activate", lambda _: self._2fa_submission_button.clicked())

        self._2fa_spinner = Gtk.Spinner()
        self._2fa_form.attach_next_to(
            self._2fa_spinner, self._2fa_submission_button,
            Gtk.PositionType.BOTTOM, 1, 1
        )

        self.reset()

    @GObject.Signal(name="user-logged-in")
    def user_logged_in(self):
        """Signal emitted after a successful login."""
        pass

    def reset(self):
        """Resets the state of the login/2fa forms."""
        self.error_message = ""
        self.username = ""
        self.password = ""
        self.two_factor_auth_code = ""
        # Avoid that the focus is on the text entry fields because when that's
        # the case, the text entry placeholder is not shown.
        self._login_button.grab_focus()
        self._activate_form(self._login_form)

    @property
    def username(self):
        """Returns the username introduced in the login form."""
        return self._username_entry.get_text()

    @username.setter
    def username(self, username: str):
        """Sets the username in the login form."""
        self._username_entry.set_text(username)

    @property
    def password(self):
        """Returns the password introduced in the login form."""
        return self._password_entry.get_text()

    @password.setter
    def password(self, password: str):
        """Sets the password in the login form."""
        self._password_entry.set_text(password)

    def submit_login(self):
        """Submits the login form."""
        self._login_button.clicked()

    @property
    def two_factor_auth_code(self):
        """Returns the code introduced in the 2FA form."""
        return self._2fa_code_entry.get_text()

    @two_factor_auth_code.setter
    def two_factor_auth_code(self, code: str):
        """Sets the code in the 2FA form."""
        self._2fa_code_entry.set_text(code)

    def submit_two_factor_auth(self):
        """Submits the 2FA form."""
        self._2fa_submission_button.clicked()

    def is_two_factor_auth_active(self):
        """Returns True if the 2FA form is active and False otherwise."""
        return self._active_form == self._2fa_form

    @property
    def error_message(self):
        """Returns the current error message."""
        return self._error.get_text()

    @error_message.setter
    def error_message(self, message: str):
        """Sets an error message and shows it to the user."""
        self._error.set_text(message)

    def _activate_form(self, form):
        self._active_form = form
        self._stack.set_visible_child(form)

    def _on_login_button_clicked(self, _):
        self._login_spinner.start()
        future = self._controller.login(self.username, self.password)
        future.add_done_callback(self._on_login_result)

    def _on_login_result(self, future: Future[LoginResult]):
        try:
            result = future.result()
        except ValueError as e:
            self.error_message = "Invalid username."
            logger.debug(e)
            return
        except ProtonError:
            self.error_message = "Please check your internet connection."
            logger.exception("Proton API error during login.")
            return
        finally:
            self._login_spinner.stop()

        if result.success:
            logger.info("User logged in.")
            self.emit("user-logged-in")
            self.error_message = ""
        elif not result.authenticated:
            self.error_message = "Wrong password."
            logger.debug("Wrong password.")
        elif result.twofa_required:
            logger.info("Two factor auth required.")
            self._activate_form(self._2fa_form)

    def _on_2fa_submission_button_clicked(self, _):
        self._2fa_spinner.start()
        future = self._controller.submit_2fa_code(
            self.two_factor_auth_code
        )
        future.add_done_callback(self._on_2fa_submission_result)

    def _on_2fa_submission_result(self, future: Future[LoginResult]):
        try:
            result = future.result()
        except ProtonError:
            self.error_message = "Please check your internet connection."
            logger.exception("Error during 2FA.")
            return
        finally:
            self._2fa_spinner.stop()

        if result.success:
            self.emit("user-logged-in")
        elif not result.authenticated:
            self.error_message = "Session expired. Please login again."
            self._activate_form(self._login_form)
            logger.debug("Login credentials expired. Please login again.")
        elif result.twofa_required:
            self.error_message = "Wrong 2FA code."
            logger.debug("Wrong 2FA code.")
