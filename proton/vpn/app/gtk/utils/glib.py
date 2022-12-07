"""
GLib utility functions.
"""

from gi.repository import GLib


def idle_add_once(function, *args, priority=GLib.PRIORITY_DEFAULT, **kwargs):
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
