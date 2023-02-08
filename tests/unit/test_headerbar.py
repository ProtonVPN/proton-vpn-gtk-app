from concurrent.futures import Future
from unittest.mock import Mock, patch

from proton.session.exceptions import ProtonAPINotReachable
from proton.vpn.app.gtk.widgets.headerbar import HeaderBarWidget
from proton.vpn.app.gtk import Gtk

from tests.unit.utils import process_gtk_events


class TestReportBugAction:

    @patch("proton.vpn.app.gtk.widgets.headerbar.BugReportWidget")
    def test_display_successfully_bug_report_dialog(self, bug_report_patch):
        bug_dialog_mock = Mock()
        bug_report_patch.return_value = bug_dialog_mock

        headerbar_widget = HeaderBarWidget(controller=Mock(), main_window=Mock())
        headerbar_widget.bug_report_button_click()

        bug_dialog_mock.run.assert_called_once()
        bug_dialog_mock.destroy.assert_called_once()


class TestAboutAction:

    @patch("proton.vpn.app.gtk.widgets.headerbar.AboutWidget")
    def test_display_successfully_about_dialog(self, about_dialog_patch):
        about_dialog_mock = Mock()
        about_dialog_patch.return_value = about_dialog_mock

        headerbar_widget = HeaderBarWidget(controller=Mock(), main_window=Mock())
        headerbar_widget.about_button_click()

        process_gtk_events()

        about_dialog_mock.run.assert_called_once()
        about_dialog_mock.destroy.assert_called_once()


class TestLogoutAction:

    def test_successful_logout_when_not_connected_to_vpn(self):
        controller_mock = Mock()
        logout_future = Future()
        logout_future.set_result(None)

        controller_mock.logout.return_value = logout_future
        controller_mock.is_connection_active = False

        headerbar_widget = HeaderBarWidget(
            controller=controller_mock,
            main_window=Mock()
        )

        headerbar_widget.logout_button_click()

        process_gtk_events()

        controller_mock.logout.assert_called_once()

    def test_logout_reenables_logout_menu_entry_after_failed_logout_from_api(self):
        controller_mock = Mock()
        controller_mock.is_connection_active = False
        logout_future_raises_exception = Future()
        logout_future_raises_exception.set_exception(ProtonAPINotReachable("test"))
        controller_mock.logout.return_value = logout_future_raises_exception

        headerbar_widget = HeaderBarWidget(controller=controller_mock, main_window=Mock())

        headerbar_widget.logout_button_click()

        assert not headerbar_widget.logout_enabled

        process_gtk_events()

        controller_mock.logout.assert_called_once()
        assert headerbar_widget.logout_enabled

    
    def test_logout_displays_unable_to_logout_message_after_failed_logout_from_api(self):
        main_window_mock = Mock()
        controller_mock = Mock()
        controller_mock.is_connection_active = False
        logout_future_raises_exception = Future()
        logout_future_raises_exception.set_exception(ProtonAPINotReachable("test"))
        controller_mock.logout.return_value = logout_future_raises_exception

        headerbar_widget = HeaderBarWidget(controller=controller_mock, main_window=main_window_mock)
        headerbar_widget.logout_button_click()

        process_gtk_events()

        controller_mock.logout.assert_called_once()
        main_window_mock.main_widget.show_error_message.assert_called_once_with(
            headerbar_widget.UNABLE_TO_LOGOUT_MESSAGE,
            True, headerbar_widget.UNABLE_TO_LOGOUT_TITLE
        )

    @patch("proton.vpn.app.gtk.widgets.headerbar.DisconnectDialog")
    def test_successful_logout_after_user_dialog_confirmation_while_connected_to_vpn(self, disconnect_widget):
        controller_mock = Mock()
        logout_future = Future()
        logout_future.set_result(None)

        controller_mock.logout.return_value = logout_future
        controller_mock.is_connection_active = True

        disconnect_dialog_mock = Mock()
        disconnect_dialog_mock.run.return_value = Gtk.ResponseType.YES.real
        disconnect_widget.return_value = disconnect_dialog_mock

        headerbar_widget = HeaderBarWidget(
            controller=controller_mock,
            main_window=Mock()
        )

        headerbar_widget.logout_button_click()

        process_gtk_events()

        disconnect_dialog_mock.run.assert_called_once()
        disconnect_dialog_mock.destroy.assert_called_once()
        controller_mock.logout.assert_called_once()

    @patch("proton.vpn.app.gtk.widgets.headerbar.DisconnectDialog")
    def test_logout_is_cancelled_while_connected_to_vpn_if_user_cancels_confirmation_dialog(self, disconnect_widget):
        controller_mock = Mock()
        logout_future = Future()
        logout_future.set_result(None)

        controller_mock.logout.return_value = logout_future
        controller_mock.is_connection_active = True

        disconnect_dialog_mock = Mock()
        disconnect_dialog_mock.run.return_value = Gtk.ResponseType.NO.real
        disconnect_widget.return_value = disconnect_dialog_mock

        headerbar_widget = HeaderBarWidget(
            controller=controller_mock,
            main_window=Mock()
        )

        headerbar_widget.logout_button_click()

        process_gtk_events()

        disconnect_dialog_mock.run.assert_called_once()
        disconnect_dialog_mock.destroy.assert_called_once()
        assert not controller_mock.logout.call_count


class TestQuitAction:

    def test_successful_quit(self):
        main_window_mock = Mock()
        controller_mock = Mock()
        controller_mock.is_connection_active = False

        headerbar_widget = HeaderBarWidget(
            controller=controller_mock, main_window=main_window_mock
        )

        headerbar_widget.quit_button_click()

        process_gtk_events()

        main_window_mock.destroy.assert_called_once()

    @patch("proton.vpn.app.gtk.widgets.headerbar.DisconnectDialog")
    def test_sucessfull_quit_after_user_dialog_confirmation_while_connected_to_vpn(self, disconnect_widget):
        main_window_mock = Mock()
        controller_mock = Mock()
        controller_mock.is_connection_active = True

        quit_dialog_mock = Mock()
        quit_dialog_mock.run.return_value = Gtk.ResponseType.YES.real
        disconnect_widget.return_value = quit_dialog_mock

        headerbar_widget = HeaderBarWidget(
            controller=controller_mock, main_window=main_window_mock
        )

        headerbar_widget.quit_button_click()
        main_window_mock.destroy.assert_called_once()

    @patch("proton.vpn.app.gtk.widgets.headerbar.DisconnectDialog")
    def test_quit_is_cancelled_while_connected_to_vpn_user_cancels_confirmation_dialog(self, disconnect_widget):
        main_window_mock = Mock()
        controller_mock = Mock()
        controller_mock.is_connection_active = True

        quit_dialog_mock = Mock()
        quit_dialog_mock.run.return_value = Gtk.ResponseType.NO.real
        disconnect_widget.return_value = quit_dialog_mock

        headerbar_widget = HeaderBarWidget(
            controller=controller_mock, main_window=main_window_mock
        )

        headerbar_widget.quit_button_click()
        main_window_mock.destroy.assert_not_called()
