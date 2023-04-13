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
from collections import namedtuple
from unittest.mock import Mock, patch

import pytest
from proton.session.exceptions import ProtonAPINotReachable, ProtonAPIError, \
    ProtonAPIAuthenticationNeeded

from proton.vpn.app.gtk.widgets.main.exception_handler import ExceptionHandler
from proton.vpn.app.gtk.widgets.main.main_widget import MainWidget


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


@patch("proton.vpn.app.gtk.widgets.main.exception_handler.ExceptionHandler.handle_exception")
def test_handle_thread_exception_delegates_to_handle_exception(patched_handle_exception):
    exception_handler = ExceptionHandler(main_widget=None)

    ExceptHookArgs = namedtuple("ExceptHookArgs", "exc_type exc_value exc_traceback thread")
    args = ExceptHookArgs(exc_type=Exception, exc_value=Exception(""), exc_traceback=None, thread=None)
    exception_handler.handle_thread_exception(args)

    patched_handle_exception.assert_called_once_with(args.exc_type, args.exc_value, args.exc_traceback)


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


def test_handle_authentication_needed_exception_calls_main_widget_session_expired():
    main_widget_mock = Mock(MainWidget)
    exception_handler = ExceptionHandler(main_widget=main_widget_mock)

    exception_handler.handle_exception(
        exc_type=ProtonAPIAuthenticationNeeded,
        exc_value=ProtonAPIAuthenticationNeeded(401, [], {"Code": 0, "Error": ""}),
        exc_traceback=None
    )

    main_widget_mock.session_expired.assert_called_once()


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
