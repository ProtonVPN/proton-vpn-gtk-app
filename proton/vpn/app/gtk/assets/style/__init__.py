"""All the icons the app uses are available in this module."""
from pathlib import Path

from gi.repository import Gdk, Gtk

STYLE_PATH = Path(__file__).parent


def load_app_css(display: Gdk.Display) -> None:
    """Load the app's CSS into `display` at application priority.

    Shared by App and DemoApp so demo screens are styled identically to what
    real users see.
    """
    css_provider = Gtk.CssProvider()
    css_provider.load_from_path(str(STYLE_PATH / "main.css"))
    Gtk.StyleContext.add_provider_for_display(
        display,
        css_provider,
        Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
    )
