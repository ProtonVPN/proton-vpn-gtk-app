"""Loads the app's stylesheets."""
from pathlib import Path
from typing import List, Optional, Tuple

from gi.repository import Gdk, Gtk

STYLE_PATH = Path(__file__).parent

# Styles for GTK's built-in widgets (buttons, switches, entries, ...).
PRIMITIVES_CSS = STYLE_PATH / "_primitives.css"
PALETTE_CSS = STYLE_PATH / "_dark_palette.css"
MAIN_CSS = STYLE_PATH / "main.css"

# Primitives priority is below main.css, so main.css's per-widget (ID) rules win.
# Palette priority is above main.css, so its colours replace the dark_colours.css ones
# main.css imports.
PRIMITIVES_PRIORITY = Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION - 1
MAIN_PRIORITY = Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
PALETTE_PRIORITY = Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION + 1


def app_css_paths() -> List[Tuple[Path, int]]:
    """Stylesheets to load, each as a separate provider, with its priority."""
    return [
        (PRIMITIVES_CSS, PRIMITIVES_PRIORITY),
        (MAIN_CSS, MAIN_PRIORITY),
        (PALETTE_CSS, PALETTE_PRIORITY),
    ]


def load_app_css(
    display: Gdk.Display, paths: Optional[List[Tuple[Path, int]]] = None
) -> None:
    """Load the app's CSS into `display`.

    Shared by App and DemoApp so demo screens are styled identically to what
    real users see.

    Each stylesheet is a separate provider, so the primitives can be removed
    while the app is running without unloading main.css.

    :param paths: stylesheets and priorities to load, app_css_paths() by default.
    """
    for path, priority in paths or app_css_paths():
        provider = Gtk.CssProvider()
        provider.load_from_path(str(path))
        Gtk.StyleContext.add_provider_for_display(display, provider, priority)
