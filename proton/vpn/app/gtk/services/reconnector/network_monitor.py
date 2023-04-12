"""
Network connectivity monitoring.
"""
import subprocess
from concurrent.futures import ThreadPoolExecutor, Future
from typing import Callable

from gi.repository import GLib

from proton.vpn import logging  # noqa: E402 # pylint: disable=wrong-import-position
from proton.vpn.app.gtk.utils.glib import run_once, run_periodically

logger = logging.getLogger(__name__)


def check_for_network_connectivity() -> bool:
    """
    Checks for network connectivity and returns True if connected or False otherwise.
    """
    # 192.0.2.1 is used because is a valid IP that won't be in use,
    # since it is reserved for documentation purposes:
    # https://www.rfc-editor.org/rfc/rfc5737.html
    result = subprocess.run(["ip", "route", "get", "192.0.2.1"], check=False, capture_output=True)
    return result.returncode == 0


class NetworkMonitor:
    """
    After being enabled, it calls the callback set on the network_up_callback
    attribute whenever connectivity to the Internet is detected.

    Note that it requires a GLib main loop to be running, as the current
    implementation relies on it to poll for network state changes.

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

    def __init__(self, pool: ThreadPoolExecutor, polling_interval_ms: int = 5000):
        self._pool = pool
        self._polling_interval_ms = polling_interval_ms
        self._is_network_up = None
        self._polling_handler_id = None
        self.network_up_callback: Callable = None

    def enable(self):
        """
        Enables the network connectivity monitor.

        It runs the `check_network_state_async` method periodically on the GLib main loop.
        """
        self._polling_handler_id = run_periodically(
            interval_ms=self._polling_interval_ms,
            function=self.check_network_state_async
        )

    def disable(self):
        """Disables the network connectivity monitor."""
        if self._polling_handler_id is not None:
            GLib.source_remove(self._polling_handler_id)
            self._polling_handler_id = None
        self._is_network_up = None

    def check_network_state_async(self) -> Future:
        """Checks what's the network state."""
        return self._pool.submit(self._poll_network_state)

    def _poll_network_state(self):

        network_up = check_for_network_connectivity()
        network_just_went_up = not self.is_network_up and network_up
        self._is_network_up = network_up

        if network_just_went_up and self.network_up_callback:
            run_once(self.network_up_callback)

    @property
    def is_network_up(self) -> bool:
        """
        Returns True if the device is connected to the network or False otherwise.
        Note: the value returned is based on the last check_network_state_async call.
        """
        return self._is_network_up

    @property
    def is_enabled(self) -> bool:
        """Returns whether the network monitor is enabled or not."""
        return self._polling_handler_id is not None
