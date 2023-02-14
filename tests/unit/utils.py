import sys

from gi.repository import GLib

from proton.vpn.app.gtk import Gtk


def raise_main_loop_exceptions(func):
    """
    Decorator intended to be used on test code running exclusively on GLib's main loop.

    To avoid that the main loop crashes, GLib swallows any unhandled exceptions. Because of this,
    tests running code on GLib's main loop may not be aware of unhandled exceptions happening
    the tests.

    However, if the test function uses this decorator then, once the test function returns control,
    any exceptions happening while the GLib's main loop was running will be raised.


    """
    def wrapper(*args, **kwargs):
        original_excepthook = sys.excepthook
        exceptions = []

        def unhandled_exception_hook(exc_type, exc_value, exc_traceback):
            exceptions.append((exc_type, exc_value, exc_traceback))

        try:
            # To avoid that the main loop crashes, GLib swallows any unhandled exceptions.
            # We plug an exception hook to detect unhandled exceptions caught by GLib's
            # main exception handler, so that then we can reraise them later.
            sys.excepthook = unhandled_exception_hook

            return func(*args, **kwargs)
        finally:
            sys.excepthook = original_excepthook

            # Reraise any unhandled exceptions caught by GLib's main exception handler
            # so that tests are aware they happened.
            if exceptions:
                exc_type, exc_value, exc_traceback = exceptions[0]

                raise exc_value.with_traceback(exc_traceback)

    return wrapper


@raise_main_loop_exceptions
def process_gtk_events():
    """Processes all pending GTK events."""
    while Gtk.events_pending():
        Gtk.main_iteration_do(blocking=False)


@raise_main_loop_exceptions
def run_main_loop(main_loop, timeout_in_seconds=5):
    timeout_occurred = False

    def signal_timeout_and_quit_main_loop():
        nonlocal timeout_occurred
        timeout_occurred = True
        main_loop.quit()

    GLib.timeout_add_seconds(timeout_in_seconds, signal_timeout_and_quit_main_loop)
    main_loop.run()

    if timeout_occurred:
        raise RuntimeError(f"Timeout occurred after {timeout_in_seconds} seconds.")
