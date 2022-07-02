from asyncio import Future
from concurrent.futures import ThreadPoolExecutor

from proton.vpn.connection.enum import ConnectionStateEnum
from proton.vpn.core_api import ProtonVPNAPI
from proton.vpn.session.dataclasses import LoginResult
from proton.vpn.core_api.connection import Subscriber


class Controller:
    """The C in the MVC pattern."""
    def __init__(self, thread_pool_executor: ThreadPoolExecutor):
        self._thread_pool = thread_pool_executor
        self._api = ProtonVPNAPI()
        self._connection_subscriber = Subscriber()
        self._api.connection.register(self._connection_subscriber)

    def login(self, username: str, password: str) -> Future[LoginResult]:
        return self._thread_pool.submit(
            self._api.login,
            username, password
        )

    def submit_2fa_code(self, code: str) -> Future[LoginResult]:
        return self._thread_pool.submit(
            self._api.submit_2fa_code,
            code
        )

    def logout(self):
        return self._thread_pool.submit(self._api.logout)

    def connect(self):
        def _connect():
            server = self._api.servers.get_server_with_features(
                servername="NL#3"
            )
            self._api.connection.connect(server, protocol="openvpn-udp")
            self._connection_subscriber.wait_for_state(
                ConnectionStateEnum.CONNECTED, timeout=10
            )
        return self._thread_pool.submit(_connect)

    def disconnect(self):
        def _disconnect():
            self._api.connection.disconnect()
            self._connection_subscriber.wait_for_state(
                ConnectionStateEnum.DISCONNECTED, timeout=5
            )
        return self._thread_pool.submit(_disconnect)
