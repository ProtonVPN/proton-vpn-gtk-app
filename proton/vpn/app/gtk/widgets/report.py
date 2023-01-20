"""
Issue report module.
"""
from __future__ import annotations

import io
from concurrent.futures import Future
import re

from typing import TYPE_CHECKING
from gi.repository import Gtk, GLib

from proton.session.exceptions import ProtonAPINotReachable, ProtonAPIError
from proton.vpn.core_api.reports import BugReportForm
import proton.vpn.app.gtk as app
from proton.vpn import logging

if TYPE_CHECKING:
    from proton.vpn.app.gtk.controller import Controller

logger = logging.getLogger(__name__)


class BugReportWidget(Gtk.Dialog):  # pylint: disable=too-many-instance-attributes
    """Widget used to report bug/issues to Proton."""
    WIDTH = 400
    HEIGHT = 300
    EMAIL_REGEX = re.compile(
        r'([A-Za-z0-9]+[.-_])*[A-Za-z0-9]+@[A-Za-z0-9-]+(\.[A-Z|a-z]{2,})+'
    )
    BUG_REPORT_SENDING_MESSAGE = "Sending bug report..."
    BUG_REPORT_SUCCESS_MESSAGE = "Report sent successfully\n"\
                                 "(this window will close automatically)"
    BUG_REPORT_NETWORK_ERROR_MESSAGE = "Proton services could not be reached.\n" \
                                       "Please try again."
    BUG_REPORT_UNEXPECTED_ERROR_MESSAGE = "Something went wrong. " \
                                          "Please try submitting your report at:\n" \
                                          "https://protonvpn.com/support-form"

    def __init__(self, controller: Controller, main_window: Gtk.ApplicationWindow):
        super().__init__(transient_for=main_window)
        self.controller = controller

        self.set_title("Report an Issue")
        self.set_default_size(BugReportWidget.WIDTH, BugReportWidget.HEIGHT)

        self.add_button("_Cancel", Gtk.ResponseType.CANCEL)
        self.add_button("_Submit", Gtk.ResponseType.OK)

        self.connect("response", self._on_response)
        self.connect("realize", lambda _: self.show_all())  # pylint: disable=no-member

        self._generate_fields()
        self.set_response_sensitive(Gtk.ResponseType.OK, False)

    @property
    def status_label(self) -> str:
        """Returns submission status"""
        return self._submission_status_label.get_text()

    @status_label.setter
    def status_label(self, newvalue: str):
        self._submission_status_label.set_text(newvalue if newvalue else "")
        self._submission_status_label.set_property("visible", bool(newvalue))

    def _on_response(
        self, dialog: BugReportWidget,
        response: Gtk.ResponseType
    ):  # pylint: disable=unused-argument
        """Upon any of the button being clicked in the dialog,
        it's responde is evaluated.
        """
        if response != Gtk.ResponseType.OK:
            self.close()
            return

        self.status_label = self.BUG_REPORT_SENDING_MESSAGE

        report_form = BugReportForm(
            username=self.username_entry.get_text(),
            email=self.email_entry.get_text(),
            title=self.title_entry.get_text(),
            description=self.description_buffer.get_text(
                self.description_buffer.get_start_iter(),
                self.description_buffer.get_end_iter(),
                True
            ),
            client_version=app.__version__,
            client="GUI/Desktop",
        )

        if self.send_logs_checkbox.get_active():
            report_form.attachments.append(LogCollector.get_app_log(logger))

        self._disable_form()
        future = self.controller.submit_bug_report(report_form)
        future.add_done_callback(
            lambda future: GLib.idle_add(
                self._on_report_submission_result,
                future
            )
        )

    def _on_report_submission_result(self, future: Future):
        try:
            future.result()
        except ProtonAPINotReachable:
            logger.warning("Report submission failed: API not reachable.")
            self.status_label = self.BUG_REPORT_NETWORK_ERROR_MESSAGE
            self._enable_form()
        except ProtonAPIError as exc:
            # ProtonAPIError is raised when the backend considers the email
            # address is not valid (some addresses like test@test.com are banned).
            logger.warning(f"Proton API error: {exc}")
            self.status_label = exc.error
            self._enable_form()
        except Exception:  # pylint: disable=broad-except
            self.status_label = self.BUG_REPORT_UNEXPECTED_ERROR_MESSAGE
            self._enable_form()
            logger.exception("Unexpected error submitting bug report.")
        else:
            self.status_label = self.BUG_REPORT_SUCCESS_MESSAGE
            GLib.timeout_add_seconds(
                interval=3,
                function=self.close
            )

        return False

    def _disable_form(self):
        self.username_entry.set_sensitive(False)
        self.email_entry.set_sensitive(False)
        self.title_entry.set_sensitive(False)
        self.description_textview.set_sensitive(False)
        self.send_logs_checkbox.set_sensitive(False)
        self.set_response_sensitive(Gtk.ResponseType.OK, False)

    def _enable_form(self):
        self.username_entry.set_sensitive(True)
        self.email_entry.set_sensitive(True)
        self.title_entry.set_sensitive(True)
        self.description_textview.set_sensitive(True)
        self.send_logs_checkbox.set_sensitive(True)
        if self._can_user_submit_form:
            self.set_response_sensitive(Gtk.ResponseType.OK, True)

    def _on_entry_changed(self, _: Gtk.Widget):
        self.set_response_sensitive(
            Gtk.ResponseType.OK, self._can_user_submit_form
        )

    @property
    def _can_user_submit_form(self) -> bool:
        is_username_provided = len(self.username_entry.get_text().strip()) > 0
        is_email_provided = re.fullmatch(
            self.EMAIL_REGEX, self.email_entry.get_text()
        )
        is_title_provided = len(self.title_entry.get_text().strip()) > 0
        is_description_provided = len(self.description_buffer.get_text(
            self.description_buffer.get_start_iter(),
            self.description_buffer.get_end_iter(),
            True
        )) > 10

        return bool(
            is_username_provided
            and is_email_provided
            and is_title_provided
            and is_description_provided
        )

    def _generate_fields(self):  # pylint: disable=too-many-statements
        """Generates the necessary fields for the report."""
        fields_vbox = Gtk.Box.new(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        fields_vbox.set_spacing(3)

        self._submission_status_label = Gtk.Label.new(None)
        self._submission_status_label.set_name("error_label")
        self._submission_status_label.set_no_show_all(True)  # pylint: disable=no-member
        self._submission_status_label.set_justify(Gtk.Justification.CENTER)
        self._submission_status_label.set_line_wrap(True)
        # set_max_width_chars is required for set_line_wrap to have effect.
        self._submission_status_label.set_max_width_chars(1)
        self._submission_status_label.set_property("margin-bottom", 10)
        fields_vbox.add(self._submission_status_label)  # pylint: disable=no-member

        username_label = Gtk.Label.new("Username")
        username_label.set_halign(Gtk.Align.START)
        self.username_entry = Gtk.Entry.new()
        self.username_entry.set_property("margin-bottom", 10)
        self.username_entry.set_input_purpose(Gtk.InputPurpose.FREE_FORM)
        self.username_entry.set_name("username")
        fields_vbox.add(username_label)  # pylint: disable=no-member
        fields_vbox.add(self.username_entry)  # pylint: disable=no-member

        email_label = Gtk.Label.new("Email")
        email_label.set_halign(Gtk.Align.START)
        self.email_entry = Gtk.Entry.new()
        self.email_entry.set_property("margin-bottom", 10)
        self.email_entry.set_input_purpose(Gtk.InputPurpose.EMAIL)
        self.email_entry.set_name("email")
        fields_vbox.add(email_label)  # pylint: disable=no-member
        fields_vbox.add(self.email_entry)  # pylint: disable=no-member

        title_label = Gtk.Label.new("Title")
        title_label.set_halign(Gtk.Align.START)
        self.title_entry = Gtk.Entry.new()
        self.title_entry.set_property("margin-bottom", 10)
        self.title_entry.set_input_purpose(Gtk.InputPurpose.ALPHA)
        self.title_entry.set_name("title")
        fields_vbox.add(title_label)  # pylint: disable=no-member
        fields_vbox.add(self.title_entry)  # pylint: disable=no-member

        description_label = Gtk.Label.new("Description")
        description_label.set_halign(Gtk.Align.START)
        # Has to have min 10 chars
        self.description_buffer = Gtk.TextBuffer.new(None)
        self.description_textview = Gtk.TextView.new_with_buffer(
            self.description_buffer
        )
        self.description_textview.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self.description_textview.set_input_purpose(Gtk.InputPurpose.FREE_FORM)
        self.description_textview.set_justification(Gtk.Justification.FILL)
        self.description_textview.set_name("description")
        scrolled_window_textview = Gtk.ScrolledWindow()
        scrolled_window_textview.set_property("margin-bottom", 10)
        scrolled_window_textview.set_min_content_height(100)
        scrolled_window_textview.add(self.description_textview)  # pylint: disable=no-member
        fields_vbox.add(description_label)  # pylint: disable=no-member
        fields_vbox.add(scrolled_window_textview)  # pylint: disable=no-member

        self.send_logs_checkbox = Gtk.CheckButton.new_with_label("Send error logs")
        self.send_logs_checkbox.set_active(True)
        self.send_logs_checkbox.set_name("send_logs")
        fields_vbox.add(self.send_logs_checkbox)  # pylint: disable=no-member

        # By default Gtk.Dialog has a vertical box child (Gtk.Box)
        self.vbox.add(fields_vbox)  # pylint: disable=no-member
        self.vbox.set_border_width(20)  # pylint: disable=no-member
        self.vbox.set_spacing(20)  # pylint: disable=no-member

        self.username_entry.connect(
            "changed", self._on_entry_changed
        )
        self.email_entry.connect(
            "changed", self._on_entry_changed
        )
        self.title_entry.connect(
            "changed", self._on_entry_changed
        )
        self.description_buffer.connect(
            "changed", self._on_entry_changed
        )

    def click_on_submit_button(self):
        """This method emulates the click on the 'Submit' button.
        This method is used mainly for testing purposes.
        """
        self._on_response(self, Gtk.ResponseType.OK)


class LogCollector:  # pylint: disable=too-few-public-methods
    """Collects all necessary logs needed for the report tool."""

    @staticmethod
    def get_app_log(_logger: logger) -> io.IOBase:
        """Get app log"""
        root_logger = _logger.logger.root
        for handler in root_logger.handlers:
            if handler.__class__.__name__ == "RotatingFileHandler":
                return open(handler.baseFilename, "rb")

        raise RuntimeError("App logs not found.")
