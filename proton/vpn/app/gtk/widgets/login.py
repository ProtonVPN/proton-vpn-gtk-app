import os
import logging
from concurrent.futures import Future

from gi.repository import GObject, GdkPixbuf, GLib

from proton.vpn.session.dataclasses import LoginResult

from proton.vpn.app.gtk.controller import Controller
from proton.vpn.app.gtk import Gtk


logger = logging.getLogger(__name__)


class LoginWidget(Gtk.Stack):
    """Widget used to authenticate the user."""
    def __init__(self, controller: Controller):
        super().__init__()
        self._controller = controller
        self.active_form = None

        self.login_form = LoginForm(controller)
        self.add_named(self.login_form, "login_form")
        self.two_factor_auth_form = TwoFactorAuthForm(controller)
        self.add_named(self.two_factor_auth_form, "2fa_form")

        self.login_form.connect(
            "user-authenticated",
            lambda _, two_factor_auth_required:
            self._on_user_authenticated(two_factor_auth_required)
        )

        self.two_factor_auth_form.connect(
            "two-factor-auth-successful",
            lambda _: self._on_two_factor_auth_successful()
        )

        self.two_factor_auth_form.connect(
            "session-expired",
            lambda _: self._on_session_expired_during_2fa()
        )

    def _on_user_authenticated(self, two_factor_auth_required: bool):
        if not two_factor_auth_required:
            self._signal_user_logged_in()
        else:
            self.display_form(self.two_factor_auth_form)

    def _on_two_factor_auth_successful(self):
        self._signal_user_logged_in()

    def _on_session_expired_during_2fa(self):
        self.display_form(self.login_form)

    @GObject.Signal(name="user-logged-in")
    def user_logged_in(self):
        """Signal emitted after a successful login."""
        pass

    def _signal_user_logged_in(self):
        self.emit("user-logged-in")

    def display_form(self, form):
        self.active_form = form
        self.set_visible_child(form)
        form.reset()

    def reset(self):
        self.display_form(self.login_form)


class LoginForm(Gtk.Grid):
    def __init__(self, controller: Controller):
        super().__init__(row_spacing=10, column_spacing=10)
        self._controller = controller

        self.set_column_homogeneous(True)
        self._setup_icons()

        self._error = Gtk.Label(label="")
        self.add(self._error)

        self._username_entry = Gtk.Entry()
        self._username_entry.set_placeholder_text("Username")
        self.attach_next_to(
            self._username_entry, self._error,
            Gtk.PositionType.BOTTOM, 1, 1)

        self._password_entry = Gtk.Entry()
        self._password_entry.set_placeholder_text("Password")
        self._password_entry.set_visibility(False)
        self.attach_next_to(
            self._password_entry, self._username_entry,
            Gtk.PositionType.BOTTOM, 1, 1)

        self._login_button = Gtk.Button(label="Login")
        self._login_button.connect("clicked", self._on_login_button_clicked)
        self.attach_next_to(
            self._login_button, self._password_entry,
            Gtk.PositionType.BOTTOM, 1, 1
        )
        # Pressing enter on the password entry triggers the clicked event
        # on the login button.
        self._password_entry.connect(
            "activate", lambda _: self._login_button.clicked())

        self._login_spinner = Gtk.Spinner()
        self.attach_next_to(
            self._login_spinner, self._login_button,
            Gtk.PositionType.BOTTOM, 1, 1
        )

        # Set password visibility
        self._password_entry.set_icon_from_pixbuf(
            Gtk.EntryIconPosition.SECONDARY,
            self._show_pixbuff
        )
        self._password_entry.set_icon_activatable(
            Gtk.EntryIconPosition.SECONDARY,
            True
        )
        self._password_entry.connect(
            "icon-press", self.on_change_password_visibility
        )

        self.reset()

    def _on_login_button_clicked(self, _):
        self._login_spinner.start()
        future = self._controller.login(self.username, self.password)
        future.add_done_callback(
            lambda future: GLib.idle_add(self._on_login_result, future)
        )

    def _on_login_result(self, future: Future[LoginResult]):
        try:
            result = future.result()
        except ValueError as e:
            self.error_message = "Invalid username."
            logger.debug(e)
            self.emit("login-error")
            return
        finally:
            self._login_spinner.stop()

        if result.authenticated:
            self._signal_user_authenticated(result.twofa_required)
        else:
            self.error_message = "Wrong credentials."
            self.emit("login-error")
            logger.debug(self.error_message)

    def _signal_user_authenticated(self, two_factor_auth_required: bool):
        self.emit("user-authenticated", two_factor_auth_required)
        self.reset()

    @GObject.Signal(name="user-authenticated", arg_types=(bool,))
    def user_authenticated(self, two_factor_auth_required: bool):
        """
        Signal emitted after the user successfully authenticates.
        :param two_factor_auth_required: whether 2FA is required or not.
        """
        pass

    @GObject.Signal(name="login-error")
    def login_error(self):
        """Signal emitted when a login error occurred."""
        pass

    def reset(self):
        """Resets the state of the login/2fa forms."""
        self.error_message = ""
        self.username = ""
        self.password = ""
        # Avoid that the focus is on the text entry fields because when that's
        # the case, the text entry placeholder is not shown. Find a better way.
        self._login_button.grab_focus()

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

    @property
    def error_message(self):
        """Returns the current error message."""
        return self._error.get_text()

    @error_message.setter
    def error_message(self, message: str):
        """Sets an error message and shows it to the user."""
        self._error.set_text(message)

    def submit_login(self):
        """Submits the login form."""
        self._login_button.clicked()

    def on_change_password_visibility(
        self, gtk_entry_object, gtk_icon_object, gtk_event
    ):
        is_text_visible = gtk_entry_object.get_visibility()
        gtk_entry_object.set_visibility(not is_text_visible)
        self._password_entry.set_icon_from_pixbuf(
            Gtk.EntryIconPosition.SECONDARY,
            self._show_pixbuff
            if is_text_visible
            else self._hide_pixbuff
        )

    def _setup_icons(self):
        eye_dirpath = os.path.dirname(os.path.abspath(__file__)).split("/")
        eye_dirpath.pop()
        eye_dirpath.append("assets")
        eye_dirpath.append("icons")
        eye_dirpath.append("eye")
        eye_dirpath = "/".join(eye_dirpath)
        hide_fp = os.path.join(eye_dirpath, "hide.svg")
        show_fp = os.path.join(eye_dirpath, "show.svg")

        self._hide_pixbuff = GdkPixbuf.Pixbuf.new_from_file_at_scale(
            filename=hide_fp,
            width=18,
            height=18,
            preserve_aspect_ratio=True
        )
        self._show_pixbuff = GdkPixbuf.Pixbuf.new_from_file_at_scale(
            filename=show_fp,
            width=18,
            height=18,
            preserve_aspect_ratio=True
        )


class TwoFactorAuthForm(Gtk.Grid):
    def __init__(self, controller: Controller):
        super().__init__(row_spacing=10, column_spacing=10)
        self._controller = controller

        self.set_column_homogeneous(True)

        self._error = Gtk.Label(label="")
        self.add(self._error)

        self._2fa_code_entry = Gtk.Entry()
        self._2fa_code_entry.set_placeholder_text("Insert your 2FA code here")
        self.attach_next_to(
            self._2fa_code_entry, self._error,
            Gtk.PositionType.BOTTOM, 1, 1)

        self._2fa_submission_button = Gtk.Button(label="Submit 2FA code")
        self._2fa_submission_button.connect(
            "clicked", self._on_2fa_submission_button_clicked
        )
        self.attach_next_to(
            self._2fa_submission_button, self._2fa_code_entry,
            Gtk.PositionType.BOTTOM, 1, 1)
        # Pressing enter on the password entry triggers the clicked event
        # on the login button.
        self._2fa_code_entry.connect(
            "activate", lambda _: self._2fa_submission_button.clicked())

        self._2fa_spinner = Gtk.Spinner()
        self.attach_next_to(
            self._2fa_spinner, self._2fa_submission_button,
            Gtk.PositionType.BOTTOM, 1, 1
        )

        self.reset()

    def _on_2fa_submission_button_clicked(self, _):
        self._2fa_spinner.start()
        future = self._controller.submit_2fa_code(
            self.two_factor_auth_code
        )
        future.add_done_callback(
            lambda future: GLib.idle_add(self._on_2fa_submission_result, future)
        )

    def _on_2fa_submission_result(self, future: Future[LoginResult]):
        try:
            result = future.result()
        finally:
            self._2fa_spinner.stop()

        if not result.authenticated:
            self.error_message = "Session expired. Please login again."
            self.emit("session-expired")
            logger.debug(self.error_message)
        elif result.twofa_required:
            self.error_message = "Wrong 2FA code."
            logger.debug(self.error_message)
        else:  # authenticated and 2FA not required
            self._signal_two_factor_auth_successful()

    def _signal_two_factor_auth_successful(self):
        self.emit("two-factor-auth-successful")
        self.reset()

    @GObject.Signal
    def two_factor_auth_successful(self):
        """Signal emitted after a successful 2FA."""
        pass

    @GObject.Signal
    def session_expired(self):
        """Signal emitted when the session expired and the user has to log in again."""

    def reset(self):
        """Resets the state of the login/2fa forms."""
        self.error_message = ""
        self.two_factor_auth_code = ""
        # Avoid that the focus is on the text entry fields because when that's
        # the case, the text entry placeholder is not shown. Find a better way.
        self._2fa_submission_button.grab_focus()

    @property
    def error_message(self):
        """Returns the current error message."""
        return self._error.get_text()

    @error_message.setter
    def error_message(self, message: str):
        """Sets an error message and shows it to the user."""
        self._error.set_text(message)

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
