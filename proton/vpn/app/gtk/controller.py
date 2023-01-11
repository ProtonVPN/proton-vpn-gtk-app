"""
This module defines the Controller class, which decouples the GUI from the
Proton VPN back-ends.
"""
from concurrent.futures import ThreadPoolExecutor, Future

from proton.vpn.connection import VPNConnection, states
from proton.vpn.core_api.api import ProtonVPNAPI
from proton.vpn.core_api.connection import Subscriber, VPNConnectionHolder
from proton.vpn.servers.server_types import LogicalServer

from proton.vpn.app.gtk.services import VPNDataRefresher, VPNReconnector
from proton.vpn.app.gtk.widgets.report import BugReportForm


class Controller:
    """The C in the MVC pattern."""
    connection_protocol = "openvpn-udp"

    def __init__(
        self,
        thread_pool_executor: ThreadPoolExecutor,
        api: ProtonVPNAPI = None,
        vpn_data_refresher: VPNDataRefresher = None,
        vpn_reconnector: VPNReconnector = None,
    ):
        self._thread_pool = thread_pool_executor
        self._api = api or ProtonVPNAPI()
        self._connection_subscriber = Subscriber()
        self._api.connection.register(self._connection_subscriber)
        self.vpn_data_refresher = vpn_data_refresher or VPNDataRefresher(
            self._thread_pool, self._api
        )
        self.reconnector = vpn_reconnector or VPNReconnector(
            self._api.connection, self.vpn_data_refresher
        )

    def login(self, username: str, password: str) -> Future:
        """
        Logs the user in.
        :param username:
        :param password:
        :return: A Future object wrapping the result of the login API call.
        """
        return self._thread_pool.submit(
            self._api.login,
            username, password
        )

    def submit_2fa_code(self, code: str) -> Future:
        """
        Submits a 2-factor authentication code for verification.
        :param code: The 2FA code.
        :return: A Future object wrapping the result of the 2FA verification.
        """
        return self._thread_pool.submit(
            self._api.submit_2fa_code,
            code
        )

    def logout(self) -> Future:
        """
        Logs the user out.
        :return: A future to be able to track the logout completion.
        """
        return self._thread_pool.submit(self._api.logout)

    @property
    def user_logged_in(self) -> bool:
        """
        Returns whether the user is logged in or not.
        :return: True if the user is logged in. Otherwise, False.
        """
        return self._api.is_user_logged_in()

    @property
    def user_tier(self):
        """Returns user tier."""
        return self._api.get_user_tier()

    def connect_to_country(self, country_code: str):
        """
        Establishes a VPN connection to the specified country.
        :param country_code: The ISO3166 code of the country to connect to.
        :return: A Future object that resolves once the connection reaches the
        "connected" state.
        """
        server = self._api.servers.get_server_by_country_code(country_code)
        self._connect_to_vpn(server)

    def connect_to_fastest_server(self):
        """
        Establishes a VPN connection to the fastest server.
        :return: A Future object that resolves once the connection reaches the
        "connected" state.
        """
        server = self._api.servers.get_fastest_server()
        self._connect_to_vpn(server)

    def connect_to_server(self, server_name: str = None):
        """
        Establishes a VPN connection.
        :param server_name: The name of the server to connect to.
        :return: A Future object that resolves once the connection reaches the
        "connected" state.
        """
        server = self._api.servers.get_vpn_server_by_name(servername=server_name)
        self._connect_to_vpn(server)

    def _connect_to_vpn(self, server: LogicalServer):
        vpn_server = self._api.connection.get_vpn_server(
            server, self.vpn_data_refresher.client_config
        )
        self._api.connection.connect(
            vpn_server,
            protocol=self.connection_protocol
        )

    def disconnect(self):
        """
        Terminates a VPN connection.
        :return: A Future object that resolves once the connection reaches the
        "disconnected" state.
        """
        self._api.connection.disconnect()

    @property
    def current_connection(self) -> VPNConnection:
        """Returns the current VPN connection, if it exists."""
        return self._api.connection.current_connection

    @property
    def current_connection_status(self) -> states.BaseState:
        """Returns the current VPN connection status. If there is not a
        current VPN connection, then the Disconnected state is returned."""
        if self.is_connection_active:
            return self.current_connection.status

        return states.Disconnected()

    @property
    def is_connection_active(self) -> bool:
        """Returns whether the current connection is in connecting/connected state or not."""
        return self._api.connection.is_connection_active

    def submit_bug_report(self, report_form: BugReportForm) -> Future:
        """Submits an issue report.
        :return: A Future object wrapping the result of the API."""
        return self._thread_pool.submit(
            self._api.bug_report.submit,
            report_form
        )

    def register_connection_status_subscriber(self, subscriber):
        """
        Registers a new subscriber to connection status updates.
        :param subscriber: The subscriber to be registered.
        """
        self._api.connection.register(subscriber)

    def unregister_connection_status_subscriber(self, subscriber):
        """
        Unregisters an existing subscriber from connection status updates.
        :param subscriber: The subscriber to be unregistered.
        """
        self._api.connection.unregister(subscriber)

    @property
    def vpn_connector(self) -> VPNConnectionHolder:
        """Returns the VPN connector"""
        return self._api.connection
