"""Loads the app's stylesheets."""
from pathlib import Path
from typing import List

from gi.repository import Gdk, Gtk

STYLE_PATH = Path(__file__).parent

# Styles for GTK's built-in widgets (buttons, switches, entries, ...).
PRIMITIVES_CSS = STYLE_PATH / "_primitives.css"
MAIN_CSS = STYLE_PATH / "main.css"


def app_css_paths() -> List[Path]:
    """Stylesheets to load, in order. Each one is loaded as a separate provider.

    _primitives.css must come first. When two providers with the same priority
    set the same property on a widget, GTK uses the value from the provider
    added last, regardless of selector specificity. main.css has rules for
    individual widgets (selected by ID) that must override the rules for whole
    widget types (e.g. all buttons) in _primitives.css.
    """
    return [PRIMITIVES_CSS, MAIN_CSS]


def load_app_css(display: Gdk.Display) -> None:
    """Load the app's CSS into `display` at application priority.

    Shared by App and DemoApp so demo screens are styled identically to what
    real users see.

    Each stylesheet is a separate provider, so _primitives.css can be removed
    while the app is running without unloading main.css.
    """
    for path in app_css_paths():
        css_provider = Gtk.CssProvider()
        css_provider.load_from_path(str(path))
        Gtk.StyleContext.add_provider_for_display(
            display,
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
