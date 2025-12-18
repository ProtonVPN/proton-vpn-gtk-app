from unittest.mock import Mock, PropertyMock, patch
from tests.unit.testing_utils import process_gtk_events
from proton.vpn.app.gtk.widgets.headerbar.menu.settings.account_settings import AccountSettings, CustomButton


@patch("proton.vpn.app.gtk.widgets.headerbar.menu.settings.account_settings.Gio.AppInfo.launch_default_for_uri")
def test_account_settings_ensure_url_is_opened_when_clicking_on_button(show_uri_on_window_mock):
    controller_mock = Mock()

    controller_mock.account_name = "test account name"
    controller_mock.account_data.plan_title = "Free"

    account_settings = AccountSettings(controller_mock)
    account_settings.build_ui()
    custom_button = account_settings.get_last_child()
    custom_button.button.emit("clicked")

    process_gtk_events()

    show_uri_on_window_mock.assert_called_once()
