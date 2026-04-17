from unittest.mock import Mock, patch
import pytest

from proton.vpn.app.gtk.controller import Controller
from proton.vpn.session.dataclasses import NPSSurveyResponse


MockOpenVPNTCP = Mock(name="MockOpenVPNTCP")
MockOpenVPNTCP.protocol = "openvpn-tcp"
MockOpenVPNTCP.ui_protocol = "OpenVPN (TCP)"
MockOpenVPNUDP = Mock(name="MockOpenVPNUDP")
MockOpenVPNUDP.protocol = "openvpn-udp"
MockOpenVPNUDP.ui_protocol = "OpenVPN (UDP)"
MockWireGuard = Mock(name="MockWireGuard")
MockWireGuard.protocol = "wireguard"
MockWireGuard.ui_protocol = "WireGuard"


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
        exception_handler=Mock(),
        api=Mock(),
        vpn_reconnector=Mock(),
        app_config=app_configuration_mock
    )

    with patch.object(controller, method_name) as mock_method:
        controller.autoconnect()

        if call_arg:
            mock_method.assert_called_once_with(call_arg) 
        else:
            mock_method.assert_called_once()


def test_submit_nps_survey_response_delegates_to_api():
    mock_executor = Mock()
    mock_api = Mock()
    controller = Controller(
        executor=mock_executor,
        exception_handler=Mock(),
        api=mock_api,
        vpn_reconnector=Mock(),
        app_config=Mock()
    )
    nps_response = Mock(NPSSurveyResponse)

    controller.submit_nps_survey_response(nps_response)

    mock_executor.submit.assert_called_once_with(mock_api.submit_nps_response, nps_response)


def test_set_notification_seen_delegates_to_api():
    mock_api = Mock()
    controller = Controller(
        executor=Mock(),
        exception_handler=Mock(),
        api=mock_api,
        vpn_reconnector=Mock(),
        app_config=Mock()
    )

    controller.set_notification_seen("survey-123")

    mock_api.set_notification_seen.assert_called_once_with("survey-123")


@patch("proton.vpn.app.gtk.controller.Controller.get_settings")
def test_get_available_protocols_returns_list_of_protocols_which_includes_wireguard_when_feature_flag_is_disabled_and_selected_protocol_is_wireguard(mock_get_settings):
    mock_connector = Mock()
    mock_api = Mock()
    controller = Controller(
        executor=Mock(),
        exception_handler=Mock(),
        api=Mock(),
        vpn_reconnector=Mock(),
        app_config=Mock(),
        vpn_connector=mock_connector
    )
    mock_get_settings.return_value.protocol = MockWireGuard.protocol
    mock_api.refresher.feature_flags.get.return_value = False
    mock_connector.iter_available_protocols.return_value = [MockOpenVPNUDP, MockOpenVPNTCP, MockWireGuard]
    protocols = controller.get_available_protocols("generic")
    assert MockWireGuard in protocols


@patch("proton.vpn.app.gtk.controller.Controller.get_settings")
def test_get_available_protocols_returns_list_of_protocols_which_includes_wireguard_when_feature_flag_is_enabled_and_selected_protocol_is_openvpn(mock_get_settings):
    mock_connector = Mock()
    mock_api = Mock()
    controller = Controller(
        executor=Mock(),
        exception_handler=Mock(),
        api=mock_api,
        vpn_reconnector=Mock(),
        app_config=Mock(),
        vpn_connector=mock_connector
    )
    mock_get_settings.return_value.protocol = MockOpenVPNTCP.protocol
    mock_api.refresher.feature_flags.get.return_value = True
    mock_connector.iter_available_protocols.return_value = [MockOpenVPNUDP, MockOpenVPNTCP, MockWireGuard]
    protocols = controller.get_available_protocols("generic")
    assert MockWireGuard in protocols
