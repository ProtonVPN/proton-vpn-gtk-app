from asyncio import Future
from concurrent.futures import ThreadPoolExecutor

from proton.vpn.connection.enum import ConnectionStateEnum
from proton.vpn.core_api import ProtonVPNAPI
from proton.vpn.core_api.connection import Subscriber


class Controller:
    """The C in the MVC pattern."""
    def __init__(self, thread_pool_executor: ThreadPoolExecutor):
        self._thread_pool = thread_pool_executor
        self._api = ProtonVPNAPI()
        self._connection_subscriber = Subscriber()
        self._api.connection.register(self._connection_subscriber)

    def login(self, username: str, password: str) -> Future:
        return self._thread_pool.submit(
            self._api.login,
            username, password
        )

    def submit_2fa_code(self, code: str) -> Future:
        return self._thread_pool.submit(
            self._api.submit_2fa_code,
            code
        )

    def logout(self) -> Future:
        return self._thread_pool.submit(self._api.logout)

    @property
    def user_logged_in(self) -> bool:
        return self._api.is_user_logged_in()

    def connect(self) -> Future:
        def _connect():
            server = self._api.servers.get_server_with_features(
                servername="NL#3"
            )
            self._api.connection.connect(server, protocol="openvpn-udp")
            self._connection_subscriber.wait_for_state(
                ConnectionStateEnum.CONNECTED, timeout=10
            )
        return self._thread_pool.submit(_connect)

    def disconnect(self) -> Future:
        def _disconnect():
            self._api.connection.disconnect()
            self._connection_subscriber.wait_for_state(
                ConnectionStateEnum.DISCONNECTED, timeout=5
            )
        return self._thread_pool.submit(_disconnect)

    def does_current_connection_exists(self) -> Future:
        def _current_connection_exists():
            return bool(self._api.connection.get_current_connection())
        return self._thread_pool.submit(_current_connection_exists)

    def get_server_list(self, force_refresh=False) -> Future:
        return self._thread_pool.submit(
            self._api.servers.get_server_list,
            force_refresh=force_refresh
        )
