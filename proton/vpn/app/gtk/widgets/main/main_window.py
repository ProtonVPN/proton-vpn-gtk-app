"""
This module defines the main application window.


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
import logging
from typing import Optional

from gi.repository import GLib, Gtk

from proton.session.exceptions import ProtonAPINotReachable, ProtonAPIError
from proton.vpn.app.gtk.controller import Controller
from proton.vpn.app.gtk.exceptions import NPSError
from proton.vpn.app.gtk.utils.safe_signal_connect import safe_signal_connect
from proton.vpn.app.gtk.widgets.main.main_widget import MainWidget
from proton.vpn.app.gtk.widgets.headerbar.headerbar import HeaderBar
from proton.vpn.app.gtk.widgets.main.notification_bar import NotificationBar
from proton.vpn.app.gtk.widgets.main.notifications import Notifications
from proton.vpn.app.gtk.widgets.main.loading_widget import OverlayWidget
from proton.vpn.app.gtk.widgets.main.pull_notifications.nps_survey_modal import \
    NPSSurveyModal
from proton.vpn.session.dataclasses import NPSSurveyResponse


logger = logging.getLogger(__name__)


# pylint: disable=too-many-instance-attributes
class MainWindow(Gtk.ApplicationWindow):
    """Main window."""

    WIDTH = 450
    HEIGHT = 700

    # pylint: disable=too-many-arguments
    def __init__(
            self, application: Gtk.Application,
            controller: Controller,
            notifications: Optional[Notifications] = None,
            header_bar: Optional[HeaderBar] = None,
            main_widget: Optional[MainWidget] = None,
            overlay_widget: Optional[OverlayWidget] = None
    ):
        super().__init__(application=application)
        self._application = application
        self.get_settings().props.gtk_application_prefer_dark_theme = True
        self._controller = controller
        self._close_window_handler_id: Optional[int] = None
        self._shortcut_controller: Optional[Gtk.ShortcutController] = None
        self._nps_modal: Optional[NPSSurveyModal] = None

        self._configure_window()

        self._overlay_widget = overlay_widget or OverlayWidget()

        notifications = notifications or Notifications(
            main_window=self, notification_bar=NotificationBar()
        )

        self.header_bar = header_bar or HeaderBar(
            controller=controller,
            main_window=self,
            overlay_widget=self._overlay_widget
        )
        self.set_titlebar(self.header_bar)
        self.set_title("Proton VPN")

        self.main_widget = main_widget or MainWidget(
            controller=controller,
            main_window=self,
            notifications=notifications,
            overlay_widget=self._overlay_widget
        )
        self.set_child(self.main_widget)

        safe_signal_connect(self, "notify::visible", self._display_pending_notifications)

        self.main_widget.set_visible(True)

    @property
    def application(self) -> Gtk.Application:
        """Returns Gtk.Application object which contains references to windows,
        tray indicator and other settings."""
        return self._application

    def add_keyboard_shortcut(self, target_widget: Gtk.Widget, target_signal: str, shortcut: str):
        """
        Adds a keyboard shortcut so that when pressed it causes the target signal
        to be triggered on the target widget.

        :param target_widget: The widget the keyboard shortcut will trigger the signal on.
        :param target_signal: The signal the keyboard shortcut will trigger on the target widget.
        :param shortcut: The keyboard shortcut string (e.g. "<Ctrl>q")
        """
        def callback(*_):
            target_widget.emit(target_signal)
            return True

        shortcut_trigger = Gtk.ShortcutTrigger.parse_string(shortcut)
        if shortcut_trigger is None:
            raise ValueError(f"Invalid shortcut: {shortcut}")

        shortcut_action = Gtk.CallbackAction.new(callback)
        shortcut_obj = Gtk.Shortcut.new(shortcut_trigger, shortcut_action)

        if self._shortcut_controller is None:
            self._shortcut_controller = Gtk.ShortcutController()
            self._shortcut_controller.set_scope(Gtk.ShortcutScope.LOCAL)
            self.add_controller(self._shortcut_controller)

        self._shortcut_controller.add_shortcut(shortcut_obj)

    def _configure_window(self):
        """
        Handle delete-event, set window resize restrictions...
        """
        self.set_name("main-window")
        self.set_resizable(False)
        self.set_size_request(MainWindow.WIDTH, MainWindow.HEIGHT)

    def configure_close_button_behaviour(self, tray_indicator_enabled: bool):
        """Configures the behaviour of the button to close the window
        (the x button), depending on if the tray indicator is used or not."""
        if tray_indicator_enabled:
            self._close_window_handler_id = self.configure_close_button_to_hide_window()
        else:
            self._close_window_handler_id = self.configure_close_button_to_trigger_quit_menu_entry()

    def configure_close_button_to_hide_window(self):
        """Configures the x (close window) button so that when clicked,
        the window is hidden instead closed."""
        # Handle the event emitted when the user tries to close the window.
        return safe_signal_connect(
            self,
            "close-request",
            self._on_close_button_clicked_then_hide_window
        )

    def _on_close_button_clicked_then_hide_window(self, *_) -> bool:
        """
        Instead of letting the window x button close the app, therefore
        quitting the app, the action is delegated to the Exit entry in
        the menu bar widget.
        """
        self.set_visible(False)

        # Returning True when handling the close-request stops other handlers
        # from being invoked for this event, therefore preventing the default
        # behaviour:
        # https://docs.gtk.org/gtk4/signal.Window.close-request.html
        return True

    def quit(self):
        """Closes the main window, which quits the app."""
        if self._close_window_handler_id:
            self.disconnect(self._close_window_handler_id)

        self.close()

    def configure_close_button_to_trigger_quit_menu_entry(self):
        """Configures the x (close window) button so that when clicked,
        the Exit menu entry is triggered instead."""
        # Handle the event emitted when the user tries to close the window.
        return safe_signal_connect(
            self,
            "close-request",
            self._on_close_button_clicked_then_click_quit_menu_entry
        )

    def _on_close_button_clicked_then_click_quit_menu_entry(self, *_) -> bool:
        """
        Instead of letting the x button close the app, therefore
        quitting the app, the action is delegated to the Exit entry in
        the menu bar widget, which may request confirmation to the user.
        """
        self.header_bar.menu.quit_button_click()

        # Returning True when handling the close-request stops other handlers
        # from being invoked for this event, therefore preventing the default
        # behaviour:
        # https://docs.gtk.org/gtk4/signal.Window.close-request.html
        return True

    def _display_pending_notifications(self, *_):
        if not self._controller.user_logged_in:
            # need to be logged in to submit NPS Survey response
            return

        if not self.get_visible():
            # ensure we're visible, and not going invisible
            return

        nps_notifications = self._controller.notifications.get_nps_survey_notifications()
        while nps_notifications:
            nps_survey = nps_notifications.pop()
            if not nps_survey.seen and nps_survey.is_active:
                self._controller.set_notification_seen(nps_survey.survey_id)
                GLib.idle_add(self._show_nps_survey)
                break

    def create_nps_survey_modal(self) -> NPSSurveyModal:
        """Creates the NPS survey modal."""
        def submit_nps_survey_feedback(score: int, comments: str):
            nps_user_response = NPSSurveyResponse(
                user_score=score,
                user_comments=comments,
                response_type=NPSSurveyResponse.ResponseType.SUBMIT
            )
            future = self._controller.submit_nps_survey_response(nps_user_response)
            future.add_done_callback(self._on_nps_submission_result)

        def dismiss_nps_survey():
            nps_user_response = \
                NPSSurveyResponse(response_type=NPSSurveyResponse.ResponseType.DISMISS)
            future = self._controller.submit_nps_survey_response(nps_user_response)
            future.add_done_callback(self._on_nps_submission_result)

        return NPSSurveyModal(
            self._controller,
            submit_handler=submit_nps_survey_feedback,
            dismiss_handler=dismiss_nps_survey
        )

    def _show_nps_survey(self):
        self._nps_modal = self.create_nps_survey_modal()
        self._nps_modal.set_transient_for(self)
        safe_signal_connect(self._nps_modal, "unrealize", self._on_nps_modal_unrealize)
        self._nps_modal.show()
        return GLib.SOURCE_REMOVE

    def _on_nps_modal_unrealize(self, _):
        self._nps_modal = None

    def _on_nps_submission_result(self, future: Future):
        try:
            future.result()
        except ProtonAPINotReachable:
            logger.warning("NPS survey submission failed: API not reachable.")
        except ProtonAPIError as exc:
            logger.warning("Proton API error: %s", exc)
        except Exception as exc:  # pylint: disable=broad-except
            logger.exception("Unexpected error submitting NPS survey response.")

            def _reraise_on_main_thread(exc=exc):
                raise NPSError(
                    "Unexpected error submitting NPS survey response."
                ) from exc

            GLib.idle_add(_reraise_on_main_thread)
