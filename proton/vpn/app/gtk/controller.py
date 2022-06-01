
from asyncio import Future
from concurrent.futures import ThreadPoolExecutor

from proton.vpn.core_api.session import LoginResult

from proton.vpn.core_api import ProtonVPNAPI

from proton.vpn.app.gtk.view import View


class Controller:
    def __init__(self, thread_pool_executor: ThreadPoolExecutor):
        self._thread_pool = thread_pool_executor
        self._api = ProtonVPNAPI()
        self._view = View(controller=self)

    def run(self):
        return self._view.run()

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
        return self._thread_pool.submit(self._api.connect, protocol="openvpn-udp", servername="NL#3")

    def disconnect(self):
        return self._thread_pool.submit(self._api.disconnect)
