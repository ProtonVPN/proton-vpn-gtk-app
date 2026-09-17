import pytest
from unittest.mock import Mock, patch
from tests.unit.testing_utils import process_gtk_events
from proton.vpn.app.gtk.widgets.headerbar.menu.settings.account_settings import AccountSettings


@pytest.fixture
def account_settings():
    controller = Mock()
    controller.account_name = "test account name"
    controller.account_data.plan_title = "VPN Plus"
    widget = AccountSettings(controller, Mock())
    widget.build_ui()
    yield widget
    widget.run_dispose()

@patch("proton.vpn.app.gtk.widgets.headerbar.menu.settings.account_settings.Gio.AppInfo.launch_default_for_uri")
def test_account_settings_ensure_url_is_opened_when_clicking_on_button(show_uri_on_window_mock,account_settings):
    custom_button = account_settings.get_last_child()
    custom_button.button.emit("clicked")

    process_gtk_events()

    show_uri_on_window_mock.assert_called_once()

def refresh_button(widget):
    row = widget.get_last_child()
    return row.extra_button   

def test_refresh_called_once(account_settings):
    btn = refresh_button(account_settings)
    btn.emit("clicked")
    btn.emit("clicked")
    account_settings._controller.refresh_vpn_info.assert_called_once()

def test_on_done_updates_plan_label_and_shows_info_message(account_settings):
    refresh_button(account_settings).emit("clicked")
    account_settings._controller.account_data.plan_title = "VPN Free"
    account_settings._controller.refresh_vpn_info.call_args.kwargs["on_done"](Mock())

    assert account_settings._refreshing is False
    assert account_settings._notification_bar.show_info_message.call_count == 1
    assert account_settings.get_last_child().description.get_text() == \
        "VPN plan: VPN Free"

def test_on_error_shows_error_notification(account_settings):
    refresh_button(account_settings).emit("clicked")
    account_settings._controller.refresh_vpn_info.call_args.kwargs["on_error"](
        RuntimeError)

    account_settings._notification_bar.show_error_message.assert_called_once_with(
        AccountSettings.REFRESH_ERROR_MESSAGE)
    assert account_settings._refreshing is False
