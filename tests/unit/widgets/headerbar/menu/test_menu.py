from concurrent.futures import Future
from unittest.mock import Mock, patch

from proton.session.exceptions import ProtonAPINotReachable
from proton.vpn.app.gtk.widgets.headerbar.menu.menu import Menu
from proton.vpn.app.gtk import Gtk

from tests.unit.utils import process_gtk_events


class TestReportBugMenuEntry:

    @patch("proton.vpn.app.gtk.widgets.headerbar.menu.menu.BugReportDialog")
    def test_bug_report_menu_entry_shows_bug_report_dialog_when_clicked(self, bug_report_dialog_patch):
        bug_report_dialog_mock = Mock()
        bug_report_dialog_patch.return_value = bug_report_dialog_mock

        menu = Menu(
            controller=Mock(),
            main_window=Mock(),
            notifications=Mock()
        )
        menu.bug_report_button_click()

        bug_report_dialog_mock.run.assert_called_once()
        bug_report_dialog_mock.destroy.assert_called_once()


class TestAboutMenuEntry:

    @patch("proton.vpn.app.gtk.widgets.headerbar.menu.menu.AboutDialog")
    def test_about_menu_entry_shows_about_dialog_when_clicked(self, about_dialog_patch):
        about_dialog_mock = Mock()
        about_dialog_patch.return_value = about_dialog_mock

        menu = Menu(
            controller=Mock(),
            main_window=Mock(),
            notifications=Mock()
        )
        menu.about_button_click()

        process_gtk_events()

        about_dialog_mock.run.assert_called_once()
        about_dialog_mock.destroy.assert_called_once()


class TestLogoutMenuEntry:

    def test_logout_menu_entry_logs_user_out_when_clicked_if_not_connected_to_vpn(self):
        controller_mock = Mock()
        logout_future = Future()
        logout_future.set_result(None)

        controller_mock.logout.return_value = logout_future
        controller_mock.is_connection_active = False

        menu = Menu(
            controller=controller_mock,
            main_window=Mock(),
            notifications=Mock()
        )

        menu.logout_button_click()

        process_gtk_events()

        controller_mock.logout.assert_called_once()

    def test_logout_menu_entry_is_enabled_again_after_after_it_is_clicked_and_logout_fails(self):
        controller_mock = Mock()
        controller_mock.is_connection_active = False
        logout_future_raises_exception = Future()
        logout_future_raises_exception.set_exception(ProtonAPINotReachable("test"))
        controller_mock.logout.return_value = logout_future_raises_exception

        menu = Menu(
            controller=controller_mock,
            main_window=Mock(),
            notifications=Mock()
        )

        menu.logout_button_click()

        assert not menu.logout_enabled

        process_gtk_events()

        controller_mock.logout.assert_called_once()
        assert menu.logout_enabled
    
    def test_logout_menu_entry_displays_unable_to_logout_dialog_after_failed_logout_fails(self):
        main_window_mock = Mock()
        controller_mock = Mock()
        controller_mock.is_connection_active = False
        logout_future_raises_exception = Future()
        logout_future_raises_exception.set_exception(ProtonAPINotReachable("test"))
        controller_mock.logout.return_value = logout_future_raises_exception

        menu = Menu(
            controller=controller_mock,
            main_window=main_window_mock,
            notifications=Mock()
        )
        menu.logout_button_click()

        process_gtk_events()

        controller_mock.logout.assert_called_once()
        main_window_mock.main_widget.notifications.show_error_dialog.assert_called_once_with(
            menu.UNABLE_TO_LOGOUT_MESSAGE,
            menu.UNABLE_TO_LOGOUT_TITLE
        )

    @patch("proton.vpn.app.gtk.widgets.headerbar.menu.menu.DisconnectDialog")
    def test_logout_menu_entry_logs_user_out_when_clicked_while_connected_to_vpn_only_after_user_dialog_confirmation(
            self, disconnect_dialog_patch
    ):
        controller_mock = Mock()
        logout_future = Future()
        logout_future.set_result(None)

        controller_mock.logout.return_value = logout_future
        controller_mock.is_connection_active = True

        disconnect_dialog_mock = Mock()
        disconnect_dialog_mock.run.return_value = Gtk.ResponseType.YES.real
        disconnect_dialog_patch.return_value = disconnect_dialog_mock

        menu = Menu(
            controller=controller_mock,
            main_window=Mock(),
            notifications=Mock()
        )

        menu.logout_button_click()

        process_gtk_events()

        disconnect_dialog_mock.run.assert_called_once()
        disconnect_dialog_mock.destroy.assert_called_once()
        controller_mock.logout.assert_called_once()

    @patch("proton.vpn.app.gtk.widgets.headerbar.menu.menu.DisconnectDialog")
    def test_logout_menu_entry_does_not_log_user_out_when_clicked_while_connected_to_vpn_if_user_cancels_confirmation_dialog(
            self, disconnect_widget
    ):
        controller_mock = Mock()
        logout_future = Future()
        logout_future.set_result(None)

        controller_mock.logout.return_value = logout_future
        controller_mock.is_connection_active = True

        disconnect_dialog_mock = Mock()
        disconnect_dialog_mock.run.return_value = Gtk.ResponseType.NO.real
        disconnect_widget.return_value = disconnect_dialog_mock

        menu = Menu(
            controller=controller_mock,
            main_window=Mock(),
            notifications=Mock()
        )

        menu.logout_button_click()

        process_gtk_events()

        disconnect_dialog_mock.run.assert_called_once()
        disconnect_dialog_mock.destroy.assert_called_once()
        assert not controller_mock.logout.call_count


class TestQuitMenuEntry:

    def test_quit_menu_entry_closes_app_window_when_clicked_while_not_connected_to_vpn(self):
        main_window_mock = Mock()
        controller_mock = Mock()
        controller_mock.is_connection_active = False

        menu = Menu(
            controller=controller_mock,
            main_window=main_window_mock,
            notifications=Mock()
        )

        menu.quit_button_click()

        process_gtk_events()

        main_window_mock.quit.assert_called_once()

    @patch("proton.vpn.app.gtk.widgets.headerbar.menu.menu.DisconnectDialog")
    def test_quit_menu_entry_closes_app_window_when_clicked_only_after_user_dialog_confirmation_while_connected_to_vpn(
            self, disconnect_dialog_patch
    ):
        main_window_mock = Mock()
        controller_mock = Mock()
        controller_mock.is_connection_active = True

        quit_dialog_mock = Mock()
        quit_dialog_mock.run.return_value = Gtk.ResponseType.YES.real
        disconnect_dialog_patch.return_value = quit_dialog_mock

        menu = Menu(
            controller=controller_mock,
            main_window=main_window_mock,
            notifications=Mock()
        )

        menu.quit_button_click()
        main_window_mock.quit.assert_called_once()

    @patch("proton.vpn.app.gtk.widgets.headerbar.menu.menu.DisconnectDialog")
    def test_quit_menu_entry_does_nothing_when_clicked_if_user_cancels_confirmation_dialog_while_connected_to_vpn(
            self, disconnect_dialog_patch
    ):
        main_window_mock = Mock()
        controller_mock = Mock()
        controller_mock.is_connection_active = True

        quit_dialog_mock = Mock()
        quit_dialog_mock.run.return_value = Gtk.ResponseType.NO.real
        disconnect_dialog_patch.return_value = quit_dialog_mock

        menu = Menu(
            controller=controller_mock,
            main_window=main_window_mock,
            notifications=Mock()
        )

        menu.quit_button_click()
        main_window_mock.quit.assert_not_called()
