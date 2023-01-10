import sys

from proton.vpn.app.gtk import Gtk


def process_gtk_events():
    original_excepthook = sys.excepthook
    exceptions = []

    def unhandled_exception_hook(exc_type, exc_value, exc_traceback):
        exceptions.append((exc_type, exc_value, exc_traceback))

    try:
        # To avoid that the main loop crashes, GLib swallows any unhandled exceptions.
        # We plug an exception hook to detect unhandled exceptions caught by GLib's
        # main exception handler, so that then we can reraise them later.
        sys.excepthook = unhandled_exception_hook

        # Process all pending GTK events.
        while Gtk.events_pending():
            Gtk.main_iteration_do(blocking=False)
    finally:
        sys.excepthook = original_excepthook

        # Reraise any unhandled exceptions caught by GLib's main exception handler
        # so that tests are aware they happened.
        if exceptions:
            exc_type, exc_value, exc_traceback = exceptions[0]
            raise exc_type(exc_value).with_traceback(exc_traceback)
