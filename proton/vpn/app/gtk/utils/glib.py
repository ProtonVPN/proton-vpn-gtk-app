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
import weakref
from concurrent.futures import Future
from typing import Callable

from gi.repository import GLib


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


def weak_deferred_glib_callback(
        method: Callable[[], bool], one_shot: bool = False
) -> Callable[[], bool]:
    """
    Wraps a bound method as a GLib.timeout_add(_seconds)/idle_add callback without
    letting GLib keep its owner alive: GLib holds a strong reference to the callback
    for as long as the source is scheduled, so wrapping it in a weakref.WeakMethod
    lets it become a self-removing no-op once the owner is garbage collected.

    :param method: a bound method to call when the callback fires.
    :param one_shot: if True, always returns GLib.SOURCE_REMOVE after calling the
        method, for one-shot timeouts. If False (default), propagates the method's
        own return value, for periodic timers that decide for themselves when to stop.
    """
    weak_method = weakref.WeakMethod(method)

    def callback() -> bool:
        bound_method = weak_method()
        if bound_method is None:
            return GLib.SOURCE_REMOVE
        result = bound_method()
        return GLib.SOURCE_REMOVE if one_shot else result

    return callback


def bubble_up_errors(future: Future):
    """Makes sure that any error the future resolves to bubbles up to the GLib main loop."""
    future.add_done_callback(lambda f: GLib.idle_add(f.result))


def add_done_callback(future: Future, callback: Callable[[Future], None]):
    """
    Adds a callback to be executed once the future completes, but in a way that's GLib-compatible.

    We currently use Futures to bridge between the asyncio event loop and the GLib event loop.
    When using Future.add_done_callback(callback), the callback is run by the thread
    running the asyncio loop. However, if the callback does GTK-related work, it needs to
    run on the thread running the GLib loop.

    This function takes care of wrapping the callback in a GLib.idle_add call to make sure the
    callback runs on the GLib thread.
    """
    future.add_done_callback(lambda f: GLib.idle_add(callback, f))
