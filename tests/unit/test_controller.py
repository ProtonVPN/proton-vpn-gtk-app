from unittest.mock import Mock, patch
import pytest

from proton.vpn.app.gtk.controller import Controller


@pytest.mark.parametrize(
    "connect_at_app_startup_value, app_start_on_login_widget, method_name, call_arg",
    [
        ("FASTEST", True, "connect_to_fastest_server", None),
        ("PT", False,  "connect_to_country", None),
        ("PT#1", True,  "connect_to_server", "PT#1"),
        ("PT", True,  "connect_to_country", "PT"),
    ]
)
def test_autoconnect_feature(
    connect_at_app_startup_value, app_start_on_login_widget,
    method_name, call_arg
):
    app_configuration_mock = Mock()
    app_configuration_mock.connect_at_app_startup = connect_at_app_startup_value

    controller = Controller(
        executor=Mock(),
        api=Mock(),
        vpn_data_refresher=Mock(),
        vpn_reconnector=Mock(),
        app_config=app_configuration_mock
    )

    with patch.object(controller, method_name) as mock_method:
        controller.autoconnect()

        if call_arg:
            mock_method.assert_called_once_with(call_arg) 
        else:
            mock_method.assert_called_once()
