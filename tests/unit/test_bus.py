from unittest.mock import Mock

from proton.vpn.app.gtk.widgets.bus import MessageBus
from tests.unit.utils import process_gtk_events


def test_bus_subscriber_is_notified_when_a_new_message_is_published_to_the_channel():
    bus = MessageBus()
    subscriber_a = Mock()
    bus.subscribe("channel_a", subscriber_a)

    subscriber_b = Mock()
    bus.subscribe("channel_b", subscriber_b)

    bus.publish("channel_a", "Message on channel A")
    bus.publish("channel_b", "Message", "on channel B", with_kwarg="kwarg")

    process_gtk_events()

    subscriber_a.assert_called_once_with("Message on channel A")
    subscriber_b.assert_called_once_with("Message", "on channel B", with_kwarg="kwarg")


def test_bus_subscriber_does_not_receive_further_channel_messages_when_unsubscribed():
    bus = MessageBus()
    subscriber_a = Mock()
    bus.subscribe("channel_a", subscriber_a)

    bus.unsubscribe("channel_a", subscriber_a)

    bus.publish("channel_a", "Message on channel A")

    process_gtk_events()

    subscriber_a.assert_not_called()
