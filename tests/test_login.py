import time
from concurrent.futures import Future
from unittest.mock import Mock

from proton.vpn.core_api.session import LoginResult

from proton.vpn.app.gtk import Gtk
from proton.vpn.app.gtk.widgets.login import LoginWidget


def process_gtk_events(delay=0):
    time.sleep(delay)
    while Gtk.events_pending():
        Gtk.main_iteration_do(blocking=False)


def test_login_widget_signals_when_the_user_is_logged_in():
    controller_mock = Mock()
    login_result_future = Future()
    login_result_future.set_result(
        LoginResult(success=True, authenticated=True, twofa_required=False)
    )
    controller_mock.login.return_value = login_result_future
    user_logged_in_callback = Mock()

    login_widget = LoginWidget(controller_mock)
    login_widget.connect("user-logged-in", user_logged_in_callback)

    login_widget._username_entry.set_text("username")
    login_widget._password_entry.set_text("password")
    login_widget._login_button.clicked()

    process_gtk_events()

    controller_mock.login.assert_called_once_with("username", "password")
    user_logged_in_callback.assert_called_once()


def test_login_widget_asks_for_2fa_when_required():
    controller_mock = Mock()
    login_result_future = Future()
    login_result_future.set_result(
        LoginResult(success=False, authenticated=True, twofa_required=True)
    )
    controller_mock.login.return_value = login_result_future

    login_widget = LoginWidget(controller_mock)

    login_widget._username_entry.set_text("username")
    login_widget._password_entry.set_text("password")
    login_widget._login_button.clicked()

    process_gtk_events()

    assert login_widget._active_form == login_widget._2fa_form


def test_login_widget_signals_when_the_user_is_logged_in_after_2fa():
    controller_mock = Mock()
    login_result_future = Future()
    login_result_future.set_result(
        LoginResult(success=True, authenticated=True, twofa_required=False)
    )
    controller_mock.submit_2fa_code.return_value = login_result_future
    user_logged_in_callback = Mock()

    login_widget = LoginWidget(controller_mock)
    login_widget.connect("user-logged-in", user_logged_in_callback)

    login_widget._2fa_code_entry.set_text("2fa-code")
    login_widget._2fa_submission_button.clicked()

    process_gtk_events()

    controller_mock.submit_2fa_code.assert_called_once_with("2fa-code")
    user_logged_in_callback.assert_called_once()
