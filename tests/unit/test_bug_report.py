from concurrent.futures import Future
from io import StringIO

from unittest.mock import Mock, patch

from proton.session.exceptions import ProtonAPINotReachable, ProtonAPIError
from proton.vpn.core_api.reports import BugReportForm

from proton.vpn.app.gtk import Gtk
from proton.vpn.app.gtk.widgets.report import BugReportWidget
from tests.unit.utils import process_gtk_events


@patch("proton.vpn.app.gtk.widgets.report.LogCollector")
def test_bug_report_widget_delegates_submission_to_controller_when_submit_button_is_clicked(log_collector_mock):
    controller_mock = Mock()
    future = Future()
    future.set_result(None)
    controller_mock.submit_bug_report.return_value = future
    bug_report_widget = BugReportWidget(controller_mock, Gtk.Window())

    expected_report_form = BugReportForm(
        username="test_user",
        email="email@pm.me",
        description="This is a description example",
        attachments=[StringIO("Log contents.")],
        client_version=bug_report_widget.BUG_REPORT_VERSION,
        client=bug_report_widget.BUG_REPORT_CLIENT,
        title=bug_report_widget.BUG_REPORT_TITLE,
    )

    bug_report_widget.username_entry.set_text(expected_report_form.username)
    bug_report_widget.email_entry.set_text(expected_report_form.email)
    bug_report_widget.description_buffer.set_text(expected_report_form.description)
    bug_report_widget.send_logs_checkbox.set_active(True)

    log_collector_mock.get_app_log.return_value = expected_report_form.attachments[0]

    bug_report_widget.click_on_submit_button()

    controller_mock.submit_bug_report.assert_called_once()

    submitted_form = controller_mock.submit_bug_report.call_args[0][0]

    assert submitted_form.__dict__ == expected_report_form.__dict__
    assert bug_report_widget.status_label == bug_report_widget.BUG_REPORT_SENDING_MESSAGE

    process_gtk_events()

    assert bug_report_widget.status_label == bug_report_widget.BUG_REPORT_SUCCESS_MESSAGE


@patch("proton.vpn.app.gtk.widgets.report.LogCollector")
def test_bug_report_widget_does_not_check_logs_when_logs_checkbox_is_unchecked(log_collector_mock):
    controller_mock = Mock()
    bug_report_widget = BugReportWidget(controller_mock, Gtk.Window())

    bug_report_widget.username_entry.set_text("Username")
    bug_report_widget.email_entry.set_text("me@proton.ch")
    bug_report_widget.description_buffer.set_text("Bug report description.")
    bug_report_widget.send_logs_checkbox.set_active(False)  # Checkbox to send logs is unchecked.

    log_collector_mock.get_app_log.return_value = StringIO("App logs content.")

    bug_report_widget.click_on_submit_button()

    controller_mock.submit_bug_report.assert_called_once()
    log_collector_mock.get_app_log.assert_not_called()

    submitted_form = controller_mock.submit_bug_report.call_args[0][0]

    assert submitted_form.attachments == []


@patch("proton.vpn.app.gtk.widgets.report.LogCollector")
def test_bug_report_widget_shows_error_message_when_api_is_not_reachable(_log_collector_mock):
    controller_mock = Mock()
    bug_report_widget = BugReportWidget(controller_mock, Gtk.Window())

    future = Future()
    future.set_exception(ProtonAPINotReachable("Forced error"))
    controller_mock.submit_bug_report.return_value = future

    bug_report_widget.click_on_submit_button()

    process_gtk_events()

    assert bug_report_widget.status_label == bug_report_widget.BUG_REPORT_NETWORK_ERROR_MESSAGE


@patch("proton.vpn.app.gtk.widgets.report.LogCollector")
def test_bug_report_widget_shows_error_message_on_api_error(_log_collector_mock):
    controller_mock = Mock()
    bug_report_widget = BugReportWidget(controller_mock, Gtk.Window())

    future = Future()
    api_error = ProtonAPIError(
        400, [], {"Code": 2050, "Error": "Invalid email address"}
    )
    future.set_exception(api_error)
    controller_mock.submit_bug_report.return_value = future

    bug_report_widget.click_on_submit_button()

    process_gtk_events()

    assert bug_report_widget.status_label == api_error.error


@patch("proton.vpn.app.gtk.widgets.report.LogCollector")
def test_bug_report_widget_shows_error_message_on_unexpected_errors_reaching_api(_log_collector_mock):
    controller_mock = Mock()
    bug_report_widget = BugReportWidget(controller_mock, Gtk.Window())

    future = Future()
    future.set_exception(RuntimeError("Forced error"))
    controller_mock.submit_bug_report.return_value = future

    bug_report_widget.click_on_submit_button()

    process_gtk_events()

    assert bug_report_widget.status_label == bug_report_widget.BUG_REPORT_UNEXPECTED_ERROR_MESSAGE

