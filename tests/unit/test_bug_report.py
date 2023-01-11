from io import StringIO

from proton.vpn.app.gtk import Gtk

from proton.vpn.core_api.reports import BugReportForm
from proton.vpn.app.gtk.widgets.report import BugReportWidget
import proton.vpn.app.gtk as app
from unittest.mock import Mock, patch


@patch("proton.vpn.app.gtk.widgets.report.LogCollector")
def test_submit_form_successfully_arguments_are_passed_to_controller(log_collector_mock):
    controller_mock = Mock()
    bug_report_widget = BugReportWidget(controller_mock, Gtk.Window())

    log_file = StringIO("Log contents.")

    expected_report_form = BugReportForm(
        username="test_user",
        email="email@pm.me",
        title="This is a title example",
        description="This is a description example",
        attachments=[log_file],
        client_version=app.__version__,
        client="GUI/Desktop",
    )

    bug_report_widget.username_entry.set_text(expected_report_form.username)
    bug_report_widget.email_entry.set_text(expected_report_form.email)
    bug_report_widget.title_entry.set_text(expected_report_form.title)
    bug_report_widget.description_buffer.set_text(expected_report_form.description)
    log_collector_mock.get_app_log.return_value = log_file

    bug_report_widget.click_on_submit_button()

    controller_mock.submit_bug_report.assert_called_once()

    submitted_form = controller_mock.submit_bug_report.call_args[0][0]

    assert submitted_form.__dict__ == expected_report_form.__dict__
