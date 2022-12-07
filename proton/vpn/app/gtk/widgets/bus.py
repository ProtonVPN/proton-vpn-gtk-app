"""Message bus."""
from typing import Callable, Any, List

from proton.vpn.app.gtk.utils.glib import idle_add_once


class MessageBus:
    """
    Bus to be able to share messages between UI widgets without having to couple
    them together.
    """

    def __init__(self):
        # Maps each channel id to a list of subscriber callbacks.
        self._subscribers: dict[str, List[Callable]] = {}

    def subscribe(self, channel_id: str, callback: Callable):
        """Subscribes a callback to a bus channel."""
        subscribers = self._subscribers.setdefault(channel_id, [])
        if callback not in subscribers:
            subscribers.append(callback)

    def unsubscribe(self, channel_id: str, callback: Callable):
        """Unsubscribes a callback from a bus channel."""
        subscribers = self._subscribers.get(channel_id, [])
        if callback in subscribers:
            subscribers.remove(callback)

    def publish(self, channel_id: str, *args: Any, **kwargs: Any):
        """Publishes a message (in the form of *args and **kwargs) to a
        bus channel."""
        subscribers = self._subscribers.get(channel_id, [])
        for subscriber in subscribers:
            idle_add_once(subscriber, *args, **kwargs)


# Global message bus shared by widgets.
bus = MessageBus()
