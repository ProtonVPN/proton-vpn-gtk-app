from unittest.mock import Mock, PropertyMock, patch
from tests.unit.testing_utils import process_gtk_events
from proton.vpn.app.gtk.widgets.headerbar.menu.settings.account_settings import AccountSettings

ACCOUNT_NAME = "test_user"
PLAN_TITLE = "test_plan_title"


def test_account_settings_when_is_called_upon_building_ui_elements():
    controller_mock = Mock()

    account_name_mock = PropertyMock(name="account_name", value=ACCOUNT_NAME)
    plant_title_mock = PropertyMock(name="plan_title", value=PLAN_TITLE)

    type(controller_mock).account_name = account_name_mock
    type(controller_mock.account_data).plan_title = plant_title_mock

    account_settings = AccountSettings(controller_mock)
    account_settings.build_ui()

    account_name_mock.assert_called_once()
    plant_title_mock.assert_called_once()


@patch("proton.vpn.app.gtk.widgets.headerbar.menu.settings.account_settings.Gtk.show_uri_on_window")
def test_account_settings_ensure_url_is_opened_when_clicking_on_button(show_uri_on_window_mock):
    controller_mock = Mock()

    account_name_mock = PropertyMock(name="account_name", value=ACCOUNT_NAME)
    plant_title_mock = PropertyMock(name="plan_title", value=PLAN_TITLE)

    type(controller_mock).account_name = account_name_mock
    type(controller_mock.account_data).plan_title = plant_title_mock

    account_settings = AccountSettings(controller_mock)
    account_settings.build_ui()

    account_settings.account_row.interactive_object.clicked()
    process_gtk_events()

    show_uri_on_window_mock.assert_called_once()
