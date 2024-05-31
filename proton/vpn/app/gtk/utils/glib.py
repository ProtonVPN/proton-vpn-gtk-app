"""
GLib utility functions.


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
from typing import Callable

from gi.repository import GLib

from proton.vpn.app.gtk.utils.scheduler import Scheduler

_scheduler = Scheduler()


def run_once(function: Callable, *args, priority=GLib.PRIORITY_DEFAULT, **kwargs) -> int:
    """
    Python implementation of GLib.idle_add_once, as currently is not available
    in pygobject.
    https://docs.gtk.org/glib/func.idle_add_once.html.
    """
    def wrapper_function():
        function(*args, **kwargs)
        # Returning a falsy value is required so that GLib does not keep
        # running the function over and over again.
        return False

    return GLib.idle_add(wrapper_function, priority=priority)


def run_periodically(function, *args, interval_ms: int, **kwargs) -> int:
    """
    Runs a function periodically on the GLib main loop.

    :param function: function to be called periodically
    :param *args: arguments to be passed to the function.
    :param interval_ms: interval at which the function should be called.
    :param **kwargs: keyword arguments to be passed to the function.
    """
    run_once(function, *args, **kwargs)

    def wrapper_function():
        function(*args, **kwargs)
        # True is returned so that GLib keeps running the function.
        return True

    return GLib.timeout_add(interval_ms, wrapper_function)


def run_after_seconds(function, *args, delay_seconds: int, **kwargs) -> int:
    """
    Runs a function after the specified delay (in seconds) on the GLib main loop.

    See :func:`run_after_ms`.
    """
    if not _scheduler.is_started:
        _scheduler.start()

    return _scheduler.run_after(delay_seconds, function, *args, **kwargs)


def cancel_task(task_id: int):
    """Remove task from the scheduler given its id."""
    _scheduler.cancel_task(task_id)
