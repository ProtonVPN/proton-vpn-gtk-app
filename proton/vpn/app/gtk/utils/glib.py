"""
GLib utility functions.
"""
from typing import Callable

from gi.repository import GLib


def run_once(function: Callable, *args, priority=GLib.PRIORITY_DEFAULT, **kwargs) -> int:
    """
    Python implementation of GLib.idle_add_once, as currently is not available
    in pygobject.
    https://docs.gtk.org/glib/func.idle_add_once.html.
    """
    def wrapper():
        function(*args, **kwargs)
        # Returning a falsy value is required so that GLib does not keep
        # running the function over and over again.
        return False

    return GLib.idle_add(wrapper, priority=priority)


def run_periodically(function, *args, interval_ms: int, **kwargs) -> int:
    """
    Runs a function periodically on the GLibs main loop.

    :param function: function to be called periodically
    :param *args: arguments to be passed to the function.
    :param interval_ms: interval at which the function should be called.
    :param **kwargs: keyword arguments to be passzed to the function.
    """
    run_once(function, *args, **kwargs)

    def wrapper_function():
        function(*args, **kwargs)
        # True is returned so that GLib keeps running the function.
        return True

    return GLib.timeout_add(interval_ms, wrapper_function)
