from unittest.mock import Mock

from proton.vpn.app.gtk.widgets.login.login_widget import LoginWidget
from tests.unit.utils import process_gtk_events


def test_login_widget_signals_user_logged_in_when_user_is_authenticated_and_2fa_is_not_required():
    login_widget = LoginWidget(controller=Mock())

    user_logged_in_callback = Mock()
    login_widget.connect("user-logged-in", user_logged_in_callback)

    two_factor_auth_required = False
    login_widget.login_form.emit("user-authenticated", two_factor_auth_required)

    user_logged_in_callback.assert_called_once()


def test_login_widget_asks_for_2fa_when_required():
    login_widget = LoginWidget(controller=Mock())
    two_factor_auth_required = True
    login_widget.login_form.emit("user-authenticated", two_factor_auth_required)

    process_gtk_events()

    assert login_widget.active_form == login_widget.two_factor_auth_form


def test_login_widget_switches_back_to_login_form_if_session_expires_during_2fa():
    login_widget = LoginWidget(controller=Mock())

    login_widget.display_form(login_widget.two_factor_auth_form)
    login_widget.two_factor_auth_form.emit("session-expired")

    assert login_widget.active_form == login_widget.login_form
