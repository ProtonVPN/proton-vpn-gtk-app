"""All the icons the app uses are available in this module."""
from pathlib import Path

import gi
gi.require_version("Adw", "1")
from gi.repository import Adw, Gdk, Gtk  # noqa: E402  # pylint: disable=wrong-import-position

STYLE_PATH = Path(__file__).parent

# Holds the colour tokens (@define-color), reloaded whenever the system's
# light/dark preference changes. Kept as a separate provider from the rest
# of the stylesheet so only the colour values need reloading on theme change;
# named colours resolve across providers on the same display, so the rest of
# the CSS (which only references @token names) never needs to be reparsed.
_colour_provider = Gtk.CssProvider()
_style_manager_connected = False


def _colour_scheme_filename(is_dark: bool) -> str:
    return "dark_colours.css" if is_dark else "light_colours.css"


def _load_colour_scheme(is_dark: bool) -> None:
    _colour_provider.load_from_path(
        str(STYLE_PATH / _colour_scheme_filename(is_dark))
    )


def load_app_css(display: Gdk.Display) -> None:
    """Load the app's CSS into `display` at application priority.

    Shared by App and DemoApp so demo screens are styled identically to what
    real users see.

    Colour tokens follow the system's light/dark preference (via libadwaita)
    instead of forcing dark theme, and update live if the user changes it
    while the app is running.
    """
    global _style_manager_connected  # pylint: disable=global-statement

    Adw.init()
    style_manager = Adw.StyleManager.get_default()

    _load_colour_scheme(style_manager.get_dark())
    if not _style_manager_connected:
        style_manager.connect(
            "notify::dark",
            lambda manager, _param: _load_colour_scheme(manager.get_dark())
        )
        _style_manager_connected = True

    Gtk.StyleContext.add_provider_for_display(
        display,
        _colour_provider,
        Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
    )

    css_provider = Gtk.CssProvider()
    css_provider.load_from_path(str(STYLE_PATH / "main.css"))
    Gtk.StyleContext.add_provider_for_display(
        display,
        css_provider,
        Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
    )
