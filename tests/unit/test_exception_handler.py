import sys
import threading
from collections import namedtuple
from unittest.mock import Mock, patch

import pytest
from proton.session.exceptions import ProtonAPINotReachable, ProtonAPIError, \
    ProtonAPIAuthenticationNeeded

from proton.vpn.app.gtk.widgets.exception_handler import ExceptionHandler
from proton.vpn.app.gtk.widgets.main import MainWidget


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


@patch("proton.vpn.app.gtk.widgets.exception_handler.ExceptionHandler.handle_exception")
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

        assert sys.excepthook == original_sys_excepthook
        assert threading.excepthook == original_threading_excepthook
    finally:
        sys.excepthook = original_sys_excepthook
        threading.excepthook = original_threading_excepthook


@pytest.mark.parametrize(
    "exception,error_message,blocking", [
        (ProtonAPIError(401, [], {"Code": 0, "Error": "API Error"}), "API Error", False),
        (ProtonAPINotReachable(""), ExceptionHandler.PROTON_API_NOT_REACHABLE_MESSAGE, False),
        (Exception("Unexpected error"), ExceptionHandler.EXCEPTION_ERROR_MESSAGE, True),
    ]
)
def test_handle_exceptions_showing_error_messages(
        exception, error_message, blocking
):
    main_widget_mock = Mock(MainWidget)
    exception_handler = ExceptionHandler(main_widget=main_widget_mock)

    exception_handler.handle_exception(
        exc_type=type(exception),
        exc_value=exception,
        exc_traceback=None
    )

    main_widget_mock.show_error_message.assert_called_once_with(
        error_message,
        blocking=blocking
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
