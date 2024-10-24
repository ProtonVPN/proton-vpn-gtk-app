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
import sys
import threading
from unittest.mock import Mock
from types import SimpleNamespace

import pytest
from proton.session.exceptions import ProtonAPINotReachable, ProtonAPIError, \
    ProtonAPIAuthenticationNeeded, ProtonAPIMissingScopeError

from proton.vpn.app.gtk.utils.exception_handler import ExceptionHandler
from proton.vpn.app.gtk.widgets.main.main_widget import MainWidget
from tests.unit.testing_utils import process_gtk_events


def test_enable_exception_handler_adds_excepthooks():
    exception_handler = ExceptionHandler(main_widget=None)

    original_sys_excepthook = sys.excepthook
    original_threading_excepthook = threading.excepthook
    try:
        exception_handler.enable()

        assert sys.excepthook == exception_handler.handle_exception
        assert threading.excepthook == exception_handler.handle_thread_exception
    finally:
        sys.excepthook = original_sys_excepthook
        threading.excepthook = original_threading_excepthook


def test_handle_thread_exception_delegates_to_handle_exception():
    def raise_exception():
        raise Exception("")

    thread = threading.Thread(target=raise_exception)
    main_widget = Mock()

    with ExceptionHandler(main_widget=main_widget):
        thread.start()
        thread.join()
        process_gtk_events()
        main_widget.notifications.show_error_dialog.assert_called_once()
    main_widget.notifications.show_error_dialog.assert_called_once()

def test_disable_exception_handler_removes_excepthooks():
    exception_handler = ExceptionHandler(main_widget=None)

    original_sys_excepthook = sys.excepthook
    original_threading_excepthook = threading.excepthook

    try:
        exception_handler.enable()
        exception_handler.disable()

        assert sys.excepthook is original_sys_excepthook
        assert threading.excepthook is original_threading_excepthook
    finally:
        sys.excepthook = original_sys_excepthook
        threading.excepthook = original_threading_excepthook


@pytest.mark.parametrize(
    "exception,error_message", [
        (ProtonAPIError(401, [], {"Code": 0, "Error": "API Error"}), "API Error",),
        (ProtonAPINotReachable(""), ExceptionHandler.PROTON_API_NOT_REACHABLE_MESSAGE),
    ]
)
def test_handle_exceptions_showing_error_messages(
        exception, error_message
):
    main_widget_mock = Mock()
    exception_handler = ExceptionHandler(main_widget=main_widget_mock)

    exception_handler.handle_exception(
        exc_type=type(exception),
        exc_value=exception,
        exc_traceback=None
    )

    main_widget_mock.notifications.show_error_message.assert_called_once_with(
        error_message
    )


@pytest.mark.parametrize(
    "exception,error_title,error_message", [
        (Exception("Unexpected error"), ExceptionHandler.GENERIC_ERROR_TITLE, ExceptionHandler.GENERIC_ERROR_MESSAGE),
    ]
)
def test_handle_exceptions_showing_error_dialogs(
        exception, error_title, error_message
):
    main_widget_mock = Mock()
    exception_handler = ExceptionHandler(main_widget=main_widget_mock)

    exception_handler.handle_exception(
        exc_type=type(exception),
        exc_value=exception,
        exc_traceback=None
    )

    main_widget_mock.notifications.show_error_dialog.assert_called_once_with(
        title=error_title,
        message=error_message
    )


def test_handle_authentication_needed_exception_calls_main_widget_on_session_expired():
    main_widget_mock = Mock(MainWidget)
    exception_handler = ExceptionHandler(main_widget=main_widget_mock)

    exception_handler.handle_exception(
        exc_type=ProtonAPIAuthenticationNeeded,
        exc_value=ProtonAPIAuthenticationNeeded(401, [], {"Code": 0, "Error": ""}),
        exc_traceback=None
    )

    main_widget_mock.on_session_expired.assert_called_once()


@pytest.mark.parametrize(
    "exception_type", [
        KeyboardInterrupt,  # Exception not inheriting Exception class: https://docs.python.org/3/library/exceptions.html#exception-hierarchy
        AssertionError,  # AssertionErrors used in tests should be reraised as well
    ]
)
def test_handle_exceptions_that_should_be_raised_again(exception_type):
    exception_handler = ExceptionHandler(main_widget=None)
    with pytest.raises(exception_type):
        exception_handler.handle_exception(
            exc_type=exception_type,
            exc_value=exception_type(),
            exc_traceback=None
        )

@pytest.mark.parametrize(
    "exception,error_title,error_message", [
        (Exception("Unexpected error"), ExceptionHandler.GENERIC_ERROR_TITLE, ExceptionHandler.GENERIC_ERROR_MESSAGE),
    ]
)
def test_handle_exceptions_reporting_remotely(
        exception, error_title, error_message
):
    send_error = SimpleNamespace(invoked=False)

    def send_error_to_proton(error):
        exc_type, exc_value, exc_traceback = error

        # Make sure we're sent the correct information
        assert exc_type is Exception
        assert isinstance(exc_value, Exception)

        # Make sure we were actually invoked
        send_error.invoked = True

    controller = Mock()
    controller.send_error_to_proton = send_error_to_proton

    main_widget_mock = Mock()
    exception_handler = ExceptionHandler(main_widget=main_widget_mock,
                                         controller=controller)

    exception_handler.handle_exception(
        exc_type=type(exception),
        exc_value=exception,
        exc_traceback=None
    )

    assert send_error.invoked, "send_error_to_proton not invoked"

def test_handle_exception_logs_user_out_and_shows_missing_scope_dialog_on_proton_api_missing_scope_error():
    main_widget_mock = Mock(MainWidget)
    exception_handler = ExceptionHandler(main_widget=main_widget_mock)

    missing_scope_error = ProtonAPIMissingScopeError(
        http_code=403,
        http_headers={},
        json_data={
            'Code': 86300,
            'Error': 'You need first to assign connections to your account or any other sub-account',
            'Details': {
                'Type': 'DeviceLimit',
                'Title': 'Thanks for upgrading to Professional / Visionary',
                'Body': 'To start your journey in Proton VPN please assign VPN connections to your account or any other sub-account.',
                'Hint': 'This step will just take few minutes. After that you will be able to sign in and protect all your devices.',
                'Actions': [
                    {'Code': 'AssignConnections', 'Name': 'Assign connections', 'Category': 'main_action', 'URL': '/vpn/dashboard'}
                ]
            }
        }
    )

    exception_handler.handle_exception(
        exc_type=ProtonAPIMissingScopeError,
        exc_value=missing_scope_error,
        exc_traceback=None
    )

    main_widget_mock.logout.assert_called_once()
    main_widget_mock.notifications.show_error_dialog.assert_called_once()