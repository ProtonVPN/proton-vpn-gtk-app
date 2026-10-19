"""Loads the app's stylesheets."""
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from gi.repository import Gdk, Gio, GLib, Gtk

from proton.vpn import logging
from proton.vpn.app.gtk.utils.safe_signal_connect import safe_signal_connect

logger = logging.getLogger(__name__)

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

# The first GTK version with interface colour scheme and contrast settings.
MIN_GTK_INTERFACE_SETTINGS = (4, 20)


def app_css_paths() -> List[Tuple[Path, int]]:
    """Stylesheets to load, each as a separate provider, with its priority."""
    return [
        (PRIMITIVES_CSS, PRIMITIVES_PRIORITY),
        (MAIN_CSS, MAIN_PRIORITY),
        (PALETTE_CSS, PALETTE_PRIORITY),
    ]


def load_app_css(
    display: Gdk.Display, paths: Optional[List[Tuple[Path, int]]] = None
) -> Dict[Path, Gtk.CssProvider]:
    """Load the app's CSS into `display`.

    Shared by App and DemoApp so demo screens are styled identically to what
    real users see.

    Each stylesheet is a separate provider, so the primitives can be removed
    while the app is running without unloading main.css.

    :param paths: stylesheets and priorities to load, app_css_paths() by default.
    :return: the providers, keyed by stylesheet path.
    """
    providers = {}
    for path, priority in paths or app_css_paths():
        provider = Gtk.CssProvider()
        provider.load_from_path(str(path))
        Gtk.StyleContext.add_provider_for_display(display, provider, priority)
        providers[path] = provider
    return providers


_PORTAL_BUS_NAME = "org.freedesktop.portal.Desktop"
_PORTAL_OBJECT_PATH = "/org/freedesktop/portal/desktop"
_PORTAL_SETTINGS_INTERFACE = "org.freedesktop.portal.Settings"
# Method of the settings interface that returns the value of one setting.
_PORTAL_READ = "Read"
# Signal of the settings interface, emitted when a setting changes.
_PORTAL_SETTING_CHANGED = "SettingChanged"

# Desktop settings, as (namespace, key), that ask for high contrast when activated.
_HIGH_CONTRAST_SETTINGS = (
    # The cross-desktop standard, for any desktop that provides it.
    ("org.freedesktop.appearance", "contrast"),
    # GNOME's own, which also covers GNOME versions without the standard one.
    ("org.gnome.desktop.a11y.interface", "high-contrast"),
)


class HighContrastToggle:
    """Removes a stylesheet from a display when high contrast turns on, and adds
    it back when high contrast turns off."""

    def __init__(self, display: Gdk.Display, provider: Gtk.CssProvider, priority: int):
        self._display = display
        self._provider = provider
        self._priority = priority
        self._high_contrast = False
        self._high_contrast_by_setting: Dict[Tuple[str, str], bool] = {}
        self._portal: Optional[Gio.DBusProxy] = None

    def set_high_contrast(self, enabled: bool) -> None:
        """Removes the stylesheet while `enabled`, and adds it back otherwise."""
        if enabled == self._high_contrast:
            return
        self._high_contrast = enabled
        if enabled:
            Gtk.StyleContext.remove_provider_for_display(self._display, self._provider)
        else:
            Gtk.StyleContext.add_provider_for_display(
                self._display, self._provider, self._priority
            )

    def track_desktop_contrast(self) -> None:
        """Applies the desktop's high contrast setting now and whenever it changes.

        If the desktop doesn't provide the setting, the stylesheet remains loaded.
        """
        Gio.DBusProxy.new_for_bus(
            bus_type=Gio.BusType.SESSION,
            flags=Gio.DBusProxyFlags.NONE,
            info=None,
            name=_PORTAL_BUS_NAME,
            object_path=_PORTAL_OBJECT_PATH,
            interface_name=_PORTAL_SETTINGS_INTERFACE,
            cancellable=None,
            callback=self._on_portal_ready,
        )

    def _on_portal_ready(self, _source, result: Gio.AsyncResult) -> None:
        try:
            self._portal = Gio.DBusProxy.new_for_bus_finish(result)
        except GLib.Error:
            return
        safe_signal_connect(self._portal, "g-signal", self._on_portal_signal)
        for namespace, key in _HIGH_CONTRAST_SETTINGS:
            self._portal.call(
                method_name=_PORTAL_READ, parameters=GLib.Variant("(ss)", (namespace, key)),
                flags=Gio.DBusCallFlags.NONE, timeout_msec=-1, cancellable=None,
                callback=self._on_read, user_data=(namespace, key),
            )

    def _on_read(self, portal: Gio.DBusProxy, result: Gio.AsyncResult, setting) -> None:
        namespace, key = setting
        try:
            value = portal.call_finish(result).unpack()[0]
        except GLib.Error as error:
            logger.debug(
                "Desktop setting %s %s unavailable: %s", namespace, key, error
            )
            return
        self._record(namespace, key, value)

    def _on_portal_signal(self, _portal, _sender, signal: str, parameters: GLib.Variant) -> None:
        if signal != _PORTAL_SETTING_CHANGED:
            return
        namespace, key, value = parameters.unpack()
        if (namespace, key) in _HIGH_CONTRAST_SETTINGS:
            self._record(namespace, key, value)

    def _record(self, namespace: str, key: str, value) -> None:
        self._high_contrast_by_setting[(namespace, key)] = value == 1
        self.set_high_contrast(any(self._high_contrast_by_setting.values()))
