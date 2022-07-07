from unittest.mock import Mock

from proton.vpn.app.gtk.widgets.main import MainWidget


def test_main_widget_shows_login_widget_when_user_is_not_logged_in():
    controller_mock = Mock()
    controller_mock.user_logged_in = False

    main_widget = MainWidget(controller=controller_mock)
    main_widget.initialize_visible_widget()

    assert main_widget.active_widget is main_widget.login_widget


def test_main_widget_shows_vpn_widget_when_user_has_already_logged_in():
    controller_mock = Mock()
    controller_mock.user_logged_in = True

    main_widget = MainWidget(controller=controller_mock)
    main_widget.initialize_visible_widget()

    assert main_widget.active_widget is main_widget.vpn_widget


def test_main_widget_switches_from_login_to_vpn_widget_once_the_user_has_logged_in():
    main_widget = MainWidget(controller=None)
    main_widget.active_widget = main_widget.login_widget

    main_widget.login_widget.emit("user-logged-in")

    assert main_widget.active_widget is main_widget.vpn_widget


def test_main_widget_switches_from_vpn_to_login_widget_once_the_user_has_logged_out():
    main_widget = MainWidget(controller=None)
    main_widget.active_widget = main_widget.vpn_widget

    main_widget.vpn_widget.emit("user-logged-out")

    assert main_widget.active_widget is main_widget.login_widget
