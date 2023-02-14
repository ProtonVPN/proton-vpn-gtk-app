"""This module defines the widget used to display the 2FA form."""
from concurrent.futures import Future

from gi.repository import GLib, GObject

from proton.vpn import logging

from proton.vpn.app.gtk import Gtk
from proton.vpn.app.gtk.controller import Controller
from proton.vpn.app.gtk.widgets.login.logo import ProtonVPNLogo

logger = logging.getLogger(__name__)


class TwoFactorAuthForm(Gtk.Box):
    """
    Implements the UI for two-factor authentication. Once the right 2FA code
    is provided, it emits the `two-factor-auth-successful` signal.
    """
    def __init__(self, controller: Controller):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self._controller = controller

        self._error = Gtk.Label(label="")
        self.add(self._error)

        # pylint: disable=R0801
        self.pack_start(ProtonVPNLogo(), expand=False, fill=True, padding=0)

        self._2fa_code_entry = Gtk.Entry()
        self._2fa_code_entry.set_placeholder_text("Insert your 2FA code here")
        self._2fa_code_entry.set_input_purpose(Gtk.InputPurpose.FREE_FORM)
        self.pack_start(
            self._2fa_code_entry, expand=False, fill=False, padding=0
        )

        self._2fa_submission_button = Gtk.Button(label="Submit 2FA code")
        self._2fa_submission_button.connect(
            "clicked", self._on_2fa_submission_button_clicked
        )
        self.pack_start(
            self._2fa_submission_button, expand=False, fill=False, padding=0
        )
        # Pressing enter on the password entry triggers the clicked event
        # on the login button.
        self._2fa_code_entry.connect(
            "activate", lambda _: self._2fa_submission_button.clicked())

        self._2fa_spinner = Gtk.Spinner()
        self.pack_start(self._2fa_spinner, expand=False, fill=False, padding=0)

    def _on_2fa_submission_button_clicked(self, _):
        logger.info("Clicked on login", category="UI", subcategory="LOGIN-2FA", event="CLICK")
        self._2fa_spinner.start()
        future = self._controller.submit_2fa_code(
            self.two_factor_auth_code
        )
        future.add_done_callback(
            lambda future: GLib.idle_add(self._on_2fa_submission_result, future)
        )

    def _on_2fa_submission_result(self, future: Future):
        try:
            result = future.result()
        finally:
            self._2fa_spinner.stop()

        if not result.authenticated:
            self.error_message = "Session expired. Please login again."
            logger.debug(
                self.error_message, category="APP",
                subcategory="LOGIN-2FA", event="RESULT"
            )
            self.emit("session-expired")
        elif result.twofa_required:
            self.error_message = "Wrong 2FA code."
            logger.debug(
                self.error_message, category="APP",
                subcategory="LOGIN-2FA", event="RESULT"
            )
        else:  # authenticated and 2FA not required
            self._signal_two_factor_auth_successful()

    def _signal_two_factor_auth_successful(self):
        self.emit("two-factor-auth-successful")

    @GObject.Signal
    def two_factor_auth_successful(self):
        """Signal emitted after a successful 2FA."""

    @GObject.Signal
    def session_expired(self):
        """Signal emitted when the session expired and the user has to log in again."""

    def reset(self):
        """Resets the state of the login/2fa forms."""
        self.error_message = ""
        self.two_factor_auth_code = ""
        self._2fa_code_entry.grab_focus()

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
