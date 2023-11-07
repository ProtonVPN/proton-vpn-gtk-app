"""
Issue report module.


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
from __future__ import annotations

import io
import re
import subprocess
from tempfile import NamedTemporaryFile
from concurrent.futures import Future

from typing import TYPE_CHECKING, List
from gi.repository import Gtk, GLib

from proton.session.exceptions import ProtonAPINotReachable, ProtonAPIError
from proton.vpn.session import BugReportForm
from proton.vpn.app.gtk import __version__
from proton.vpn import logging
from proton.vpn.app.gtk.utils.executor import AsyncExecutor
from proton.vpn.app.gtk.widgets.main.notification_bar import NotificationBar

if TYPE_CHECKING:
    from proton.vpn.app.gtk.controller import Controller
    from proton.vpn.app.gtk.app import MainWindow

logger = logging.getLogger(__name__)


class BugReportDialog(Gtk.Dialog):  # pylint: disable=too-many-instance-attributes
    """Widget used to report bug/issues to Proton."""
    WIDTH = 400
    HEIGHT = 300
    EMAIL_REGEX = re.compile(
        r'([A-Za-z0-9]+[.-_])*[A-Za-z0-9]+@[A-Za-z0-9-]+(\.[A-Z|a-z]{2,})+'
    )
    BUG_REPORT_SENDING_MESSAGE = "Reporting your issue..."
    BUG_REPORT_SUCCESS_MESSAGE = "Your issue has been reported"
    BUG_REPORT_NETWORK_ERROR_MESSAGE = "Proton services could not be reached.\n" \
                                       "Please try again."
    BUG_REPORT_UNEXPECTED_ERROR_MESSAGE = "Something went wrong. " \
                                          "Please try submitting your report at:\n" \
                                          "https://protonvpn.com/support-form"
    BUG_REPORT_TITLE = "Report from Linux app"
    BUG_REPORT_CLIENT = "Linux GUI"
    BUG_REPORT_VERSION = __version__

    def __init__(
        self, controller: Controller, main_window: MainWindow,
        notification_bar: NotificationBar = None, log_collector: LogCollector = None
    ):
        super().__init__()
        self.set_name("bug-report-dialog")
        self._controller = controller
        self._main_window = main_window
        self.notification_bar = notification_bar or NotificationBar()
        self._log_collector = log_collector or LogCollector(
            self._controller.executor
        )

        self.set_title("Report an Issue")
        self.set_default_size(BugReportDialog.WIDTH, BugReportDialog.HEIGHT)

        cancel_button = self.add_button("_Cancel", Gtk.ResponseType.CANCEL)
        submit_button = self.add_button("_Submit", Gtk.ResponseType.OK)

        cancel_button.get_style_context().add_class("danger")
        submit_button.get_style_context().add_class("primary")

        self.connect("response", self._on_response)
        self.connect("realize", lambda _: self.show_all())  # pylint: disable=no-member

        self._generate_fields()
        self.set_response_sensitive(Gtk.ResponseType.OK, False)

    @property
    def status_label(self) -> str:
        """Returns the current message of the notification bar."""
        return self.notification_bar.current_message

    def _on_response(self, _: BugReportDialog, response: Gtk.ResponseType):
        """Upon any of the button being clicked in the dialog,
        it's responde is evaluated.

        It first starts the background process to generate the logs and only after
        those are finished being generated, we instantiate `BugReportForm` will
        all the available data.
        """
        if response != Gtk.ResponseType.OK:
            self.close()
            return

        # Time here has to be long to account for network issues or when API is not
        # reacheable.
        self.notification_bar.show_info_message(self.BUG_REPORT_SENDING_MESSAGE, 60000)
        if self.send_logs_checkbox.get_active():
            logs_future = self._log_collector.get_logs()
            logs_future.add_done_callback(
                lambda _logs_future: GLib.idle_add(
                    self._submit_bug_report, _logs_future.result()
                )
            )
        else:
            GLib.idle_add(self._submit_bug_report, [])

        # Prevent that the window closes before receiving the API response,
        # as by default Gtk.Dialog closes after the response signal is emitted.
        # https://lazka.github.io/pgi-docs/#GObject-2.0/functions.html#GObject.signal_stop_emission_by_name
        self.stop_emission_by_name("response")

    def _submit_bug_report(self, logs: List[io.IOBase]):
        report_form = BugReportForm(
            username=self.username_entry.get_text(),
            email=self.email_entry.get_text(),
            title=self.BUG_REPORT_TITLE,
            description=self.description_buffer.get_text(
                self.description_buffer.get_start_iter(),
                self.description_buffer.get_end_iter(),
                True
            ),
            client_version=self.BUG_REPORT_VERSION,
            client=self.BUG_REPORT_CLIENT,
            attachments=logs
        )
        self._disable_form()
        future = self._controller.submit_bug_report(report_form)
        future.add_done_callback(
            lambda future: GLib.idle_add(
                self._on_report_submission_result,
                future, report_form
            )
        )

    def _on_report_submission_result(self, future: Future, report_form: BugReportForm):
        try:
            future.result()
        except ProtonAPINotReachable:
            logger.warning("Report submission failed: API not reachable.")
            self.notification_bar.show_error_message(
                self.BUG_REPORT_NETWORK_ERROR_MESSAGE
            )
            self._enable_form()
        except ProtonAPIError as exc:
            # ProtonAPIError is raised when the backend considers the email
            # address is not valid (some addresses like test@test.com are banned).
            logger.warning(f"Proton API error: {exc}")
            self.notification_bar.show_error_message(exc.error)
            self._enable_form()
        except Exception:  # pylint: disable=broad-except
            self.notification_bar.show_error_message(
                self.BUG_REPORT_UNEXPECTED_ERROR_MESSAGE
            )
            self._enable_form()
            logger.exception("Unexpected error submitting bug report.")
        else:
            self._main_window.main_widget.notifications.show_success_message(
                self.BUG_REPORT_SUCCESS_MESSAGE
            )
            self.close()
        finally:
            for attachment in report_form.attachments:
                attachment.close()

        return False

    def _disable_form(self):
        self.username_entry.set_sensitive(False)
        self.email_entry.set_sensitive(False)
        self.description_textview.set_sensitive(False)
        self.send_logs_checkbox.set_sensitive(False)
        self.set_response_sensitive(Gtk.ResponseType.OK, False)

    def _enable_form(self):
        self.username_entry.set_sensitive(True)
        self.email_entry.set_sensitive(True)
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
        is_description_provided = len(self.description_buffer.get_text(
            self.description_buffer.get_start_iter(),
            self.description_buffer.get_end_iter(),
            True
        )) > 10

        return bool(
            is_username_provided
            and is_email_provided
            and is_description_provided
        )

    def _generate_fields(self):  # pylint: disable=too-many-statements
        """Generates the necessary fields for the report."""
        layout = Gtk.Box.new(orientation=Gtk.Orientation.VERTICAL, spacing=3)
        layout.set_border_width(0)

        layout.add(self.notification_bar)
        content = Gtk.Box.new(orientation=Gtk.Orientation.VERTICAL, spacing=3)
        content.set_name("bug-report-content")
        layout.add(content)

        username_label = Gtk.Label.new("Username")
        username_label.set_halign(Gtk.Align.START)
        self.username_entry = Gtk.Entry.new()
        self.username_entry.set_property("margin-bottom", 10)
        self.username_entry.set_input_purpose(Gtk.InputPurpose.FREE_FORM)
        self.username_entry.set_name("username")
        content.add(username_label)  # pylint: disable=no-member
        content.add(self.username_entry)  # pylint: disable=no-member

        email_label = Gtk.Label.new("Email")
        email_label.set_halign(Gtk.Align.START)
        self.email_entry = Gtk.Entry.new()
        self.email_entry.set_property("margin-bottom", 10)
        self.email_entry.set_input_purpose(Gtk.InputPurpose.EMAIL)
        self.email_entry.set_name("email")
        content.add(email_label)  # pylint: disable=no-member
        content.add(self.email_entry)  # pylint: disable=no-member

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
        content.add(description_label)  # pylint: disable=no-member
        content.add(scrolled_window_textview)  # pylint: disable=no-member

        self.send_logs_checkbox = Gtk.CheckButton.new_with_label("Send error logs")
        self.send_logs_checkbox.set_active(True)
        self.send_logs_checkbox.set_name("send_logs")
        content.add(self.send_logs_checkbox)  # pylint: disable=no-member

        # By default Gtk.Dialog has a vertical box child (Gtk.Box) `vbox`
        self.vbox.add(layout)  # pylint: disable=no-member
        self.vbox.set_border_width(0)  # pylint: disable=no-member
        self.vbox.set_spacing(20)  # pylint: disable=no-member

        self.username_entry.connect(
            "changed", self._on_entry_changed
        )
        self.email_entry.connect(
            "changed", self._on_entry_changed
        )
        self.description_buffer.connect(
            "changed", self._on_entry_changed
        )

    def click_on_submit_button(self):
        """Clicks the Submit button."""
        self.get_widget_for_response(Gtk.ResponseType.OK).clicked()


class LogCollector:  # pylint: disable=too-few-public-methods
    """Collects all necessary logs needed for the report tool."""

    def __init__(self, executor: AsyncExecutor):
        self._executor = executor

    def get_logs(self) -> Future:
        """
        Generates and returns all available logs asynchronously.
        The future result is a List of file objects.
        """
        logs_future = Future()

        app_log = self._get_app_log()
        nm_log_future = self._generate_network_manager_log()
        nm_log_future.add_done_callback(
            lambda f: logs_future.set_result([app_log, f.result()])
        )

        return logs_future

    def _get_app_log(self) -> io.IOBase:
        """Get app log"""
        root_logger = logger.logger.root
        for handler in root_logger.handlers:
            if handler.__class__.__name__ == "RotatingFileHandler":
                return open(handler.baseFilename, "rb")

        raise RuntimeError("App logs not found.")

    def _generate_network_manager_log(self) -> Future:
        """Generate Network Manager logs"""
        def run_subprocess():
            with NamedTemporaryFile(
                prefix="NetworkManager-", suffix=".log", delete=False
            ) as temp_file:
                args = [
                    "journalctl", "-u", "NetworkManager", "--no-pager",
                    "--utc", "--since=-1d", "--no-hostname"
                ]
                process = subprocess.run(args, stdout=temp_file, check=False)
                if process.returncode == 0:
                    return open(temp_file.name, "rb")

                raise RuntimeError("Network Manager logs could not be generated.")

        return self._executor.submit(run_subprocess)
