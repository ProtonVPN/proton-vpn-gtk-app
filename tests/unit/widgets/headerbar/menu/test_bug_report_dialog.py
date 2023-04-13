"""
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
from concurrent.futures import Future
from io import StringIO

from unittest.mock import Mock, patch

from proton.session.exceptions import ProtonAPINotReachable, ProtonAPIError
from proton.vpn.core_api.reports import BugReportForm

from proton.vpn.app.gtk.widgets.headerbar.menu.bug_report_dialog import BugReportDialog
from tests.unit.utils import process_gtk_events


@patch("proton.vpn.app.gtk.widgets.headerbar.menu.bug_report_dialog.LogCollector")
def test_bug_report_widget_delegates_submission_to_controller_when_submit_button_is_clicked(log_collector_mock):
    controller_mock = Mock()
    future = Future()
    future.set_result(None)
    controller_mock.submit_bug_report.return_value = future
    notification_mock = Mock()
    bug_report_widget = BugReportDialog(controller=controller_mock, notifications=notification_mock)

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

    notification_mock.show_success_message.assert_called_once_with(
        bug_report_widget.BUG_REPORT_SUCCESS_MESSAGE
    )


@patch("proton.vpn.app.gtk.widgets.headerbar.menu.bug_report_dialog.LogCollector")
def test_bug_report_widget_does_not_check_logs_when_logs_checkbox_is_unchecked(log_collector_mock):
    controller_mock = Mock()
    bug_report_widget = BugReportDialog(controller=controller_mock, notifications=Mock())

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


@patch("proton.vpn.app.gtk.widgets.headerbar.menu.bug_report_dialog.LogCollector")
def test_bug_report_widget_shows_error_message_when_api_is_not_reachable(_log_collector_mock):
    controller_mock = Mock()
    bug_report_widget = BugReportDialog(controller=controller_mock, notifications=Mock())

    future = Future()
    future.set_exception(ProtonAPINotReachable("Forced error"))
    controller_mock.submit_bug_report.return_value = future

    bug_report_widget.click_on_submit_button()

    process_gtk_events()

    assert bug_report_widget.status_label == bug_report_widget.BUG_REPORT_NETWORK_ERROR_MESSAGE


@patch("proton.vpn.app.gtk.widgets.headerbar.menu.bug_report_dialog.LogCollector")
def test_bug_report_widget_shows_error_message_on_api_error(_log_collector_mock):
    controller_mock = Mock()
    bug_report_widget = BugReportDialog(controller=controller_mock, notifications=Mock())

    future = Future()
    api_error = ProtonAPIError(
        400, [], {"Code": 2050, "Error": "Invalid email address"}
    )
    future.set_exception(api_error)
    controller_mock.submit_bug_report.return_value = future

    bug_report_widget.click_on_submit_button()

    process_gtk_events()

    assert bug_report_widget.status_label == api_error.error


@patch("proton.vpn.app.gtk.widgets.headerbar.menu.bug_report_dialog.LogCollector")
def test_bug_report_widget_shows_error_message_on_unexpected_errors_reaching_api(_log_collector_mock):
    controller_mock = Mock()
    bug_report_widget = BugReportDialog(controller=controller_mock, notifications=Mock())

    future = Future()
    future.set_exception(RuntimeError("Forced error"))
    controller_mock.submit_bug_report.return_value = future

    bug_report_widget.click_on_submit_button()

    process_gtk_events()

    assert bug_report_widget.status_label == bug_report_widget.BUG_REPORT_UNEXPECTED_ERROR_MESSAGE

