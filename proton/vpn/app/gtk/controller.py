"""
This module defines the Controller class, which decouples the GUI from the
Proton VPN back-ends.


Copyright (c) 2023 Proton AG

This file is part of Proton VPN.

Proton VPN is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Proton VPN is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with ProtonVPN.  If not, see <https://www.gnu.org/licenses/>.
"""
from concurrent.futures import ThreadPoolExecutor, Future
from importlib import metadata

from proton.vpn.connection import VPNConnection, states
from proton.vpn.core_api.api import ProtonVPNAPI
from proton.vpn.core_api.session import ClientTypeMetadata
from proton.vpn.core_api.connection import VPNConnectorWrapper
from proton.vpn.core_api.cache_handler import CacheHandler
from proton.vpn.servers.server_types import LogicalServer

from proton.vpn.app.gtk.services import VPNDataRefresher, VPNReconnector
from proton.vpn.app.gtk.services.reconnector.network_monitor import NetworkMonitor
from proton.vpn.app.gtk.services.reconnector.session_monitor import SessionMonitor
from proton.vpn.app.gtk.services.reconnector.vpn_monitor import VPNMonitor
from proton.vpn.app.gtk.utils import semver
from proton.vpn.app.gtk.widgets.headerbar.menu.bug_report_dialog import BugReportForm
from proton.vpn.app.gtk.config import AppConfig, APP_CONFIG


class Controller:
    """The C in the MVC pattern."""
    connection_protocol = "openvpn-udp"

    def __init__(
        self,
        thread_pool_executor: ThreadPoolExecutor,
        api: ProtonVPNAPI = None,
        vpn_data_refresher: VPNDataRefresher = None,
        vpn_reconnector: VPNReconnector = None,
        app_config: AppConfig = None
    ):  # pylint: disable=too-many-arguments
        self.thread_pool_executor = thread_pool_executor
        self._api = api or ProtonVPNAPI(ClientTypeMetadata(
            type="gui", version=semver.from_pep440(self.app_version)
        ))
        self.vpn_data_refresher = vpn_data_refresher or VPNDataRefresher(
            self.thread_pool_executor, self._api
        )
        self.reconnector = vpn_reconnector or VPNReconnector(
            vpn_connector=self._api.connection,
            vpn_data_refresher=self.vpn_data_refresher,
            vpn_monitor=VPNMonitor(vpn_connector=self._api.connection),
            network_monitor=NetworkMonitor(pool=thread_pool_executor),
            session_monitor=SessionMonitor()
        )
        self._app_config = app_config

    def login(self, username: str, password: str) -> Future:
        """
        Logs the user in.
        :param username:
        :param password:
        :return: A Future object wrapping the result of the login API call.
        """
        return self.thread_pool_executor.submit(
            self._api.login,
            username, password
        )

    def submit_2fa_code(self, code: str) -> Future:
        """
        Submits a 2-factor authentication code for verification.
        :param code: The 2FA code.
        :return: A Future object wrapping the result of the 2FA verification.
        """
        return self.thread_pool_executor.submit(
            self._api.submit_2fa_code,
            code
        )

    def logout(self) -> Future:
        """
        Logs the user out.
        :return: A future to be able to track the logout completion.
        """
        return self.thread_pool_executor.submit(self._api.logout)

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
    def current_connection_status(self) -> states.State:
        """Returns the current VPN connection status. If there is not a
        current VPN connection, then the Disconnected state is returned."""
        return self._api.connection.current_state

    @property
    def current_server_id(self) -> str:
        """Returns the server id of the current connection."""
        return self._api.connection.current_server_id

    @property
    def is_connection_active(self) -> bool:
        """
        Returns whether the current connection is active or not.

        A connection is considered active in the connecting, connected
        and disconnecting states.
        """
        return self._api.connection.is_connection_active

    @property
    def is_connection_disconnected(self) -> bool:
        """Returns whether the current connection is in disconnected state or not."""
        return isinstance(self._api.connection.current_state, states.Disconnected)

    def submit_bug_report(self, bug_report: BugReportForm) -> Future:
        """Submits an issue report.
        :return: A Future object wrapping the result of the API."""
        return self.thread_pool_executor.submit(
            self._api.submit_bug_report,
            bug_report
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
    def vpn_connector(self) -> VPNConnectorWrapper:
        """Returns the VPN connector"""
        return self._api.connection

    @property
    def app_configuration(self) -> AppConfig:
        """Return object with app specific configurations."""
        if self._app_config is not None:
            return self._app_config

        cache_handler = CacheHandler(APP_CONFIG)
        app_config = cache_handler.load()

        if app_config is None:
            self._app_config = AppConfig.default()
            cache_handler.save(
                self._app_config.to_dict()
            )
        else:
            self._app_config = AppConfig.from_dict(app_config)

        return self._app_config

    @property
    def app_version(self) -> str:
        """Returns the current app version."""
        return metadata.version("proton-vpn-gtk-app")
