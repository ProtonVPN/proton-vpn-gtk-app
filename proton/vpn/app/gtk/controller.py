"""
This module defines the Controller class, which decouples the GUI from the
Proton VPN back-ends.
"""
from concurrent.futures import ThreadPoolExecutor, Future

from proton.vpn.connection.enum import ConnectionStateEnum
from proton.vpn.connection import VPNConnection
from proton.vpn.core_api.api import ProtonVPNAPI
from proton.vpn.core_api.connection import Subscriber


class Controller:
    """The C in the MVC pattern."""
    def __init__(
        self, thread_pool_executor: ThreadPoolExecutor,
        api: ProtonVPNAPI = None,
        connect_timeout: int = 10, disconnect_timeout: int = 5
    ):
        self._thread_pool = thread_pool_executor
        self._api = api or ProtonVPNAPI()
        self._connection_subscriber = Subscriber()
        self._api.connection.register(self._connection_subscriber)
        self._connect_timeout = connect_timeout
        self._disconnect_timeout = disconnect_timeout

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

    def connect(self, server_name: str = None) -> Future:
        """
        Establishes a VPN connection.
        :return: A Future object that resolves once the connection reaches the
        "connected" state.
        """
        def _connect():
            self._api.connection.connect(
                self._get_server(server_name),
                protocol="openvpn-udp"
            )
            self._connection_subscriber.wait_for_state(
                ConnectionStateEnum.CONNECTED,
                timeout=self._connect_timeout
            )
        return self._thread_pool.submit(_connect)

    def _get_server(self, server_name: str = None):
        """Returns either the quickest server or the server that matches
        the provided `server_name`.
        """
        if server_name:
            return self._api.servers.get_vpn_server_by_name(
                servername=server_name
            )

        return self._api.servers.get_fastest_server()

    def disconnect(self) -> Future:
        """
        Terminates a VPN connection.
        :return: A Future object that resolves once the connection reaches the
        "disconnected" state.
        """
        def _disconnect():
            self._api.connection.disconnect()
            self._connection_subscriber.wait_for_state(
                ConnectionStateEnum.DISCONNECTED,
                timeout=self._disconnect_timeout
            )
        return self._thread_pool.submit(_disconnect)

    def get_current_connection(self) -> VPNConnection:
        """Returns the current VPN connection, if it exists."""
        return self._thread_pool.submit(self._api.connection.get_current_connection)

    def get_server_list(self, force_refresh=False) -> Future:
        """
        Returns the list of Proton VPN servers.
        :param force_refresh: When False (the default), servers will be
        obtained from a cache file when it exists, and it is not expired. When
        True it will always retrieve the server list from Proton's REST API.
        :return: A Future wrapping the server list.
        """
        return self._thread_pool.submit(
            self._api.servers.get_server_list,
            force_refresh=force_refresh
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
