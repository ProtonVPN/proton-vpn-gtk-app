from unittest.mock import ANY, Mock, call, patch
import pytest

from proton.vpn.app.gtk.controller import Controller
from proton.vpn.session.dataclasses import NPSSurveyResponse
from proton.vpn.session.exceptions import ServerNotFoundError
from proton.vpn.session.servers import LogicalServer, ServerList, TierEnum


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

    api_mock = Mock()
    api_mock.refresher.feature_flags.get.return_value = False

    controller = Controller(
        executor=Mock(),
        exception_handler=Mock(),
        api=api_mock,
        vpn_reconnector=Mock(),
        app_config=app_configuration_mock
    )

    with patch.object(controller, method_name) as mock_method:
        controller.autoconnect()

        if call_arg:
            mock_method.assert_called_once_with(call_arg) 
        else:
            mock_method.assert_called_once()


def test_connect_to_country_delegates_server_selection_to_the_server_list():
    mock_api = Mock()
    controller = Controller(
        executor=Mock(),
        exception_handler=Mock(),
        api=mock_api,
        vpn_connector=Mock(),  # needed so _connect_to_vpn doesn't crash on None
        vpn_reconnector=Mock(),
        app_config=Mock()
    )

    controller.connect_to_country("US")

    mock_api.server_list.get_fastest_in_country.assert_called_once_with("US")


def _server(server_id, exit_country="US", tier=TierEnum.FREE, score=1.0, features=0):
    return LogicalServer({
        "ID": server_id,
        "Name": f"{exit_country}#{server_id}",
        "Status": 1,
        "Servers": [{"Status": 1}],
        "Score": score,
        "Tier": int(tier),
        "ExitCountry": exit_country,
        "City": "City",
        "Features": features,
    })


def _controller_with_servers(servers, current_server_id, user_tier=TierEnum.FREE):
    mock_api = Mock()
    mock_api.server_list = ServerList(user_tier=user_tier, logicals=servers)
    vpn_connector_mock = Mock(current_server_id=current_server_id)
    controller = Controller(
        executor=Mock(),
        exception_handler=Mock(),
        api=mock_api,
        vpn_connector=vpn_connector_mock,
        vpn_reconnector=Mock(),
        app_config=Mock()
    )
    return controller, vpn_connector_mock


def test_connect_to_random_server_picks_within_the_given_country():
    current_server = _server("1", exit_country="CA")
    other_server_in_country = _server("2", exit_country="CA")
    server_in_other_country = _server("3", exit_country="US")
    controller, vpn_connector_mock = _controller_with_servers(
        [current_server, other_server_in_country, server_in_other_country],
        current_server_id=current_server.id
    )

    controller.connect_to_random_server(from_country="CA")

    vpn_connector_mock.get_vpn_server.assert_called_once_with(other_server_in_country, ANY)


def test_connect_to_random_server_picks_from_any_country_when_from_country_is_none():
    current_server = _server("1", exit_country="CA")
    server_in_other_country = _server("2", exit_country="US")
    controller, vpn_connector_mock = _controller_with_servers(
        [current_server, server_in_other_country], current_server_id=current_server.id
    )

    controller.connect_to_random_server(from_country=None)

    vpn_connector_mock.get_vpn_server.assert_called_once_with(server_in_other_country, ANY)


def test_connect_to_random_server_returns_the_current_server_when_it_is_the_only_one_available():
    only_server = _server("1", exit_country="CA")
    controller, vpn_connector_mock = _controller_with_servers(
        [only_server], current_server_id=only_server.id
    )

    controller.connect_to_random_server(from_country="CA")

    vpn_connector_mock.get_vpn_server.assert_called_once_with(only_server, ANY)


def test_connect_to_random_server_never_returns_a_server_above_the_user_tier():
    current_server = _server("1", exit_country="CA", tier=TierEnum.FREE)
    paid_server = _server("2", exit_country="CA", tier=TierEnum.PLUS)
    controller, vpn_connector_mock = _controller_with_servers(
        [current_server, paid_server], current_server_id=current_server.id, user_tier=TierEnum.FREE
    )

    controller.connect_to_random_server(from_country="CA")

    vpn_connector_mock.get_vpn_server.assert_called_once_with(current_server, ANY)


def test_connect_to_random_server_raises_when_no_server_is_available():
    controller, _ = _controller_with_servers(
        [_server("1", exit_country="FR")], current_server_id="1"
    )

    with pytest.raises(ServerNotFoundError):
        controller.connect_to_random_server(from_country="CA")


def test_change_server_uses_the_country_of_the_last_country_connection():
    current_server = _server("1", exit_country="CA")
    other_server_in_country = _server("2", exit_country="CA")
    server_in_other_country = _server("3", exit_country="US")
    controller, vpn_connector_mock = _controller_with_servers(
        [current_server, other_server_in_country, server_in_other_country],
        current_server_id=current_server.id
    )
    controller.connect_to_country("CA")

    controller.change_server()

    vpn_connector_mock.get_vpn_server.assert_called_with(other_server_in_country, ANY)


def test_change_server_uses_any_country_after_connecting_to_the_fastest_server():
    current_server = _server("1", exit_country="CA")
    server_in_other_country = _server("2", exit_country="US")
    controller, vpn_connector_mock = _controller_with_servers(
        [current_server, server_in_other_country], current_server_id=current_server.id
    )
    controller.connect_to_fastest_server()

    controller.change_server()

    vpn_connector_mock.get_vpn_server.assert_called_with(server_in_other_country, ANY)


def test_change_server_uses_any_country_when_no_connection_was_requested_yet():
    current_server = _server("1", exit_country="CA")
    server_in_other_country = _server("2", exit_country="US")
    controller, vpn_connector_mock = _controller_with_servers(
        [current_server, server_in_other_country], current_server_id=current_server.id
    )

    controller.change_server()

    vpn_connector_mock.get_vpn_server.assert_called_once_with(server_in_other_country, ANY)


def test_change_server_keeps_the_scope_of_the_last_requested_connection_across_repeated_changes():
    current_server = _server("1", exit_country="CA")
    other_server_in_country = _server("2", exit_country="CA")
    server_in_other_country = _server("3", exit_country="US")
    controller, vpn_connector_mock = _controller_with_servers(
        [current_server, other_server_in_country, server_in_other_country],
        current_server_id=current_server.id
    )
    controller.connect_to_country("CA")
    vpn_connector_mock.get_vpn_server.reset_mock()

    controller.change_server()
    controller.change_server()

    assert vpn_connector_mock.get_vpn_server.call_args_list == [
        call(other_server_in_country, ANY), call(other_server_in_country, ANY)
    ]


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


def _controller(flag_enabled=False, user_tier=TierEnum.FREE, app_config=None):
    api_mock = Mock()
    api_mock.refresher.feature_flags.get.return_value = flag_enabled
    api_mock.user_tier = user_tier
    return Controller(
        executor=Mock(),
        exception_handler=Mock(),
        api=api_mock,
        vpn_reconnector=Mock(),
        app_config=app_config if app_config is not None else Mock()
    )


@pytest.mark.parametrize(
    "flag_enabled, user_tier, expected",
    [
        (True, TierEnum.FREE, True),
        (True, TierEnum.PLUS, False),
        (False, TierEnum.FREE, False),
    ]
)
def test_server_selection_requires_upgrade_combines_the_flag_and_the_user_tier(
    flag_enabled, user_tier, expected
):
    controller = _controller(flag_enabled=flag_enabled, user_tier=user_tier)

    assert controller.server_selection_requires_upgrade is expected


@pytest.mark.parametrize("target", ["FASTEST", "PT", "PT#1"])
def test_connect_at_app_startup_returns_none_when_upgrade_is_required(target):
    controller = _controller(
        flag_enabled=True, user_tier=TierEnum.FREE,
        app_config=Mock(connect_at_app_startup=target)
    )

    assert controller.connect_at_app_startup is None


@pytest.mark.parametrize("target", ["FASTEST", "PT", "PT#1"])
def test_connect_at_app_startup_returns_the_target_unchanged_when_upgrade_is_not_required(target):
    controller = _controller(
        flag_enabled=False, user_tier=TierEnum.FREE,
        app_config=Mock(connect_at_app_startup=target)
    )

    assert controller.connect_at_app_startup == target


def test_tray_pinned_servers_returns_none_when_upgrade_is_required():
    controller = _controller(
        flag_enabled=True, user_tier=TierEnum.FREE,
        app_config=Mock(tray_pinned_servers=["PT", "NL#1"])
    )

    assert controller.tray_pinned_servers is None


@pytest.mark.parametrize("pinned_servers", [None, [], ["PT", "NL#1"]])
def test_tray_pinned_servers_returns_pinned_servers_unchanged_when_upgrade_is_not_required(
    pinned_servers
):
    controller = _controller(
        flag_enabled=False, user_tier=TierEnum.FREE,
        app_config=Mock(tray_pinned_servers=pinned_servers)
    )

    assert controller.tray_pinned_servers == pinned_servers
