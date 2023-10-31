"""
Generic exception handler.


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

from proton.vpn.connection.exceptions import AuthenticationError
from proton.session.exceptions import ProtonAPINotReachable, ProtonAPIError, \
    ProtonAPIAuthenticationNeeded
from proton.vpn.session.exceptions import ServerNotFoundError
from proton.vpn import logging

logger = logging.getLogger(__name__)


class ExceptionHandler:
    """Handles generic exceptions before they bubble all the way up."""
    GENERIC_ERROR_TITLE = "Something went wrong"
    GENERIC_ERROR_MESSAGE = "We're sorry, an unexpected error occurred." \
                            "Please try again."
    SERVER_NOT_FOUND_TITLE = "Unable to find server"
    PROTON_API_NOT_REACHABLE_MESSAGE = "Our servers are not reachable. " \
                                       "Please check your internet connection."
    VPN_AUTHENTICATION_ERROR_TITLE = "VPN connection error"
    VPN_AUTHENTICATION_ERROR_MESSAGE = (
        "Proton VPN could not connect to the VPN and blocked access to Internet to protect your IP."
        "\n\nClick \"Cancel Connection\" to restore your Internet connection. "
        "If the issue persists please try to sign out and in."
    )

    def __init__(self, main_widget):
        super().__init__()
        self._main_widget = main_widget
        self._previous_sys_excepthook = sys.excepthook
        self._previous_threading_excepthook = threading.excepthook

    def enable(self):
        """
        Enables the exception handler. Note that the exception handler
        should be enabled only after the main application window has been
        presented to the user so that error dialogs can actually be shown.
        """
        self._previous_sys_excepthook = sys.excepthook
        self._previous_threading_excepthook = threading.excepthook

        # Handle exceptions bubbling up in the main thread.
        sys.excepthook = self.handle_exception

        # Handle exceptions bubbling up in threads started with Thread.run().
        # Notice that an exception raised from a thread managed by a
        # ThreadPoolExecutor won't bubble up, as the executor won't allow it.
        # In this case, make sure that you call Future.result() on the future
        # returned by ThreadPoolExecutor.submit() in the main thread
        # (e.g. using GLib.idle_add()).
        threading.excepthook = self.handle_thread_exception

    def disable(self):
        """Disables the exception handler. The exception handler should
        be disabled as soon as the main application window is closed. This
        is specially important in tests, as the python process might run
        other test code."""
        sys.excepthook = self._previous_sys_excepthook
        threading.excepthook = self._previous_threading_excepthook

    def handle_thread_exception(self, args):
        """
        When the application exception handler is enabled, this method
        is triggered on errors that happened on threads.
        :param args: dictionary passed to threading.excepthook. For more info:
        https://docs.python.org/3/library/threading.html#threading.excepthook
        """
        return self.handle_exception(args.exc_type, args.exc_value, args.exc_traceback)

    def handle_exception(self, exc_type, exc_value, exc_traceback):
        """
        When the application exception handler is enabled, this method is
        triggered on errors that were not explicitly handled by the main
        application thread.
        :param exc_type: Type of the exception.
        :param exc_value: Instance of the exception. It might be None if the
        exception was triggered using an Exception class, rather than an object
        (e.g. raise Exception, instead of raise Exception()).
        :param exc_traceback: The exception traceback.
        """
        if issubclass(exc_type, ProtonAPIAuthenticationNeeded):
            logger.warning(
                "Authentication required.",
                category="API", event="ERROR",
                exc_info=(exc_type, exc_value, exc_traceback)
            )
            self._main_widget.session_expired()
            return

        if issubclass(exc_type, ProtonAPINotReachable):
            self._on_proton_api_not_reachable(exc_type, exc_value, exc_traceback)
        elif isinstance(exc_value, ProtonAPIError) and exc_value.error:
            self._on_proton_api_error(exc_type, exc_value, exc_traceback)
        elif isinstance(exc_value, ServerNotFoundError):
            self._on_server_not_found(exc_type, exc_value, exc_traceback)
        elif isinstance(exc_value, AuthenticationError):
            self._on_vpn_authentication_error(exc_type, exc_value, exc_traceback)
        elif issubclass(exc_type, AssertionError):
            # We shouldn't catch assertion errors raised by tests.
            raise exc_value
        elif issubclass(exc_type, Exception):
            self._on_exception(exc_type, exc_value, exc_traceback)
        else:
            raise exc_value if exc_value else exc_type

    def _on_proton_api_not_reachable(self, exc_type, exc_value, exc_traceback):
        self._main_widget.notifications.show_error_message(
            self.PROTON_API_NOT_REACHABLE_MESSAGE,
        )
        logger.warning(
            "API not reachable.",
            category="API", event="ERROR",
            exc_info=(exc_type, exc_value, exc_traceback)
        )

    def _on_proton_api_error(self, exc_type, exc_value, exc_traceback):
        self._main_widget.notifications.show_error_message(exc_value.error)
        logger.error(
            exc_value.error,
            category="APP", event="ERROR",
            exc_info=(exc_type, exc_value, exc_traceback)
        )

    def _on_server_not_found(self, exc_type, exc_value, exc_traceback):
        self._main_widget.notifications.show_error_dialog(
            title=self.SERVER_NOT_FOUND_TITLE,
            message=str(exc_value)
        )
        logger.error(
            exc_value,
            category="APP", event="ERROR",
            exc_info=(exc_type, exc_value, exc_traceback)
        )

    def _on_vpn_authentication_error(self, exc_type, exc_value, exc_traceback):
        self._main_widget.notifications.show_error_dialog(
            title=self.VPN_AUTHENTICATION_ERROR_TITLE,
            message=self.VPN_AUTHENTICATION_ERROR_MESSAGE
        )

        logger.error(
            exc_value,
            category="APP", event="ERROR",
            exc_info=(exc_type, exc_value, exc_traceback)
        )

    def _on_exception(self, exc_type, exc_value, exc_traceback):
        self._main_widget.notifications.show_error_dialog(
            title=self.GENERIC_ERROR_TITLE,
            message=self.GENERIC_ERROR_MESSAGE,
        )
        logger.critical(
            "Unexpected error.",
            category="APP", event="CRASH",
            exc_info=(exc_type, exc_value, exc_traceback)
        )
