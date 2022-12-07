"""
Network connectivity monitoring.
"""
from typing import Callable

import gi
gi.require_version("NM", "1.0")
from gi.repository import NM  # noqa: E402 # pylint: disable=wrong-import-position

from proton.vpn import logging  # noqa: E402 # pylint: disable=wrong-import-position


logger = logging.getLogger(__name__)


class NetworkMonitor:
    """
    After being enabled, it calls the callback set on the network_up_callback
    attribute whenever connectivity to the Internet is detected.

    Note that it requires a GLib main loop to be running, as the current
    implementation relies on the NetworkManager client.

    Usage example:
    .. code-block:: python
        monitor = NetworkMonitor()
        monitor.network_up_callback = lambda: print("NETWORK UP")
        monitor.enable()
        GLib.MainLoop().run()  # Only required if there is not already a main loop.

    Attributes:
        network_up_callback: callable that will be called whenever connectivity
        to the Internet is detected.
    """

    def __init__(self, nm_client: NM.Client = None):
        self._nm_client = nm_client
        self._nm_handler_id = None
        self.network_up_callback: Callable = None

    def enable(self):
        """Enables the network connectivity monitor."""
        if not self._nm_client:
            self._nm_client = NM.Client.new(None)
        self._nm_handler_id = self._nm_client.connect(
            "notify::state", self._on_network_state_changed
        )

    def disable(self):
        """Disables the network connectivity monitor."""
        if self._nm_handler_id is not None:
            self._nm_client.disconnect(self._nm_handler_id)
            self._nm_handler_id = None

    @property
    def is_network_up(self):
        """Returns True if the device is connected to the Internet or False otherwise."""
        return self._nm_client.get_state() is NM.State.CONNECTED_GLOBAL

    def _on_network_state_changed(self, _nm_client, _property):
        state = self._nm_client.get_state()
        logger.debug(f"Network state changed: {state.value_name}")
        if self.is_network_up and self.network_up_callback:
            self.network_up_callback()  # pylint: disable=not-callable
