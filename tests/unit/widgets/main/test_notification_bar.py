import time

from proton.vpn.app.gtk.widgets.main.notification_bar import NotificationBar
from tests.unit.utils import process_gtk_events


def test_notification_bar_shows_error_message_and_hides_it_automatically():
    notification_bar = NotificationBar()
    notification_bar.show_error_message("My error message.", hide_after_ms=100)
    assert notification_bar.current_message == "My error message."
    time.sleep(0.2)
    process_gtk_events()
    assert notification_bar.current_message == ""
