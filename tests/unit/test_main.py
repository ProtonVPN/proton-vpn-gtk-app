from unittest.mock import Mock

from proton.vpn.app.gtk.widgets.main import MainWidget
from unittest.mock import patch


def test_main_widget_initially_shows_login_widget_if_the_user_did_not_log_in_yet():
    main_window_mock = Mock()
    controller_mock = Mock()
    controller_mock.user_logged_in = False

    main_widget = MainWidget(controller=controller_mock, main_window=Mock())
    main_widget.initialize_visible_widget()

    assert main_widget.active_widget is main_widget.login_widget


def test_main_widget_initially_shows_vpn_widget_if_the_user_had_already_logged_in():
    controller_mock = Mock()
    controller_mock.user_logged_in = True

    main_widget = MainWidget(controller=controller_mock, main_window=Mock())
    main_widget.initialize_visible_widget()

    assert main_widget.active_widget is main_widget.vpn_widget


def test_main_widget_switches_from_login_to_vpn_widget_after_login():
    main_widget = MainWidget(controller=Mock(), main_window=Mock())
    main_widget.active_widget = main_widget.login_widget

    main_widget.login_widget.emit("user-logged-in")

    assert main_widget.active_widget is main_widget.vpn_widget


def test_main_widget_switches_from_vpn_to_login_widget_after_logout():
    main_window_mock = Mock()
    main_widget = MainWidget(controller=Mock(), main_window=main_window_mock)
    main_widget.active_widget = main_widget.vpn_widget

    logout_callback = main_window_mock.headerbar_widget.connect.call_args.args[1]
    logout_callback()

    assert main_widget.active_widget is main_widget.login_widget


@patch("proton.vpn.app.gtk.widgets.main.MainWidget.show_error_message")
def test_main_widget_switches_to_login_widget_when_session_expired(patched_show_error_message):

    main_widget = MainWidget(controller=Mock(), main_window=Mock())
    main_widget.active_widget = main_widget.vpn_widget
    main_widget.session_expired()

    assert main_widget.active_widget is main_widget.login_widget
    patched_show_error_message.assert_called_once_with(
        MainWidget.SESSION_EXPIRED_ERROR_MESSAGE,
        True, MainWidget.SESSION_EXPIRED_ERROR_TITLE
    )


def test_hide_loading_widget_after_vpn_widget_is_ready():
    """The main widget should hide the loading widget whenever the vpn
    widget is ready."""
