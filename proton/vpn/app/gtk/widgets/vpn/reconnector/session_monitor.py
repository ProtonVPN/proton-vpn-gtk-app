"""
User session monitoring.
"""
from typing import Callable


class SessionMonitor:
    """
    After being enabled, it calls the callback set on the
    session_unlocked_callback attribute whenever the user session was unlocked.

    Attributes:
        session_unlocked_callback: callable that will be called when the user
        session is unlocked.
    """
    def __init__(self):
        self.session_unlocked_callback: Callable = None

    def enable(self):
        """Enables user session monitoring."""

    def disable(self):
        """Disables user session monitoring"""

    @property
    def is_session_unlocked(self):
        """Returns True if the user session is unlocked or False otherwise."""
        return True
