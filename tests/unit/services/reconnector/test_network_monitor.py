"""
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
from unittest.mock import Mock, patch
from gi.repository import GLib

from proton.vpn.app.gtk.services.reconnector.network_monitor import NetworkMonitor
from tests.unit.testing_utils import run_main_loop, DummyThreadPoolExecutor, process_gtk_events


def test_enable_runs_check_network_state_async_periodically():
    monitor = NetworkMonitor(DummyThreadPoolExecutor(), polling_interval_ms=10)

    main_loop = GLib.MainLoop()

    with patch.object(monitor, "check_network_state_async") as patched_check_network_state:
        def quit_main_loop_after_2_connectivity_checks():
            if patched_check_network_state.call_count > 2:
                main_loop.quit()
        patched_check_network_state.side_effect = quit_main_loop_after_2_connectivity_checks

        monitor.enable()

        run_main_loop(main_loop, timeout_in_ms=1000)

    assert monitor.is_enabled
    assert patched_check_network_state.call_count > 1


@patch("proton.vpn.app.gtk.services.reconnector.network_monitor.check_for_network_connectivity")
def test_check_network_state_async_calls_network_up_callback_when_network_connectivity_is_detected(
        check_for_network_connectivity_mock
):
    monitor = NetworkMonitor(DummyThreadPoolExecutor(), polling_interval_ms=10)
    monitor.network_up_callback = Mock()

    for connectivity_check_result, network_up_callback_should_be_called in [
        (False, False),  # No connectivity detected -> callback shouldn't be called.
        (True, True),    # Connectivity detected -> callback should be called.
        (True, False),   # Connectivity still detected -> callback should NOT be called.
        (False, False),  # No connectivity detected -> callback shouldn't be called.
        (True, True)     # Connectivity detected again -> callback should be called
    ]:
        check_for_network_connectivity_mock.return_value = connectivity_check_result
        future = monitor.check_network_state_async()
        future.result()
        process_gtk_events()

        assert monitor.network_up_callback.called == network_up_callback_should_be_called
        monitor.network_up_callback.reset_mock()


def test_disable_stops_running_network_state_async_periodically():
    monitor = NetworkMonitor(DummyThreadPoolExecutor(), polling_interval_ms=10)

    main_loop = GLib.MainLoop()

    with patch.object(monitor, "check_network_state_async") as patched_check_network_state:
        def disable_monitor_after_2_connectivity_checks():
            if patched_check_network_state.call_count == 2:
                monitor.disable()
                # Quit main loop 20 ms after the second network check.
                GLib.timeout_add(interval=20, function=main_loop.quit)
        patched_check_network_state.side_effect = disable_monitor_after_2_connectivity_checks

        monitor.enable()

        run_main_loop(main_loop, timeout_in_ms=1000)

    assert not monitor.is_enabled
    # Since the monitor was disabled after the second network check, only 2 network checks should have been done.
    assert patched_check_network_state.call_count == 2
