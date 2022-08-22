import time

from proton.vpn.app.gtk import Gtk


def process_gtk_events(delay=0):
    time.sleep(delay)
    while Gtk.events_pending():
        Gtk.main_iteration_do(blocking=False)
