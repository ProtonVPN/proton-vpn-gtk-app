"""
Copyright (c) 2026 Proton AG

This file is part of Proton VPN.

Proton VPN is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Proton VPN is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with ProtonVPN.  If not, see <https://www.gnu.org/licenses/>.


DemoApp: a minimal Gtk.Application for rendering demo screens.
"""
import sys
from typing import Optional

from gi.repository import Gdk, Gio, GLib

from proton.vpn.app.gtk import Gtk
from proton.vpn.app.gtk.app import CONTINUE_STARTUP, EXIT_FAILURE, EXIT_SUCCESS
from proton.vpn.app.gtk.assets.style import load_app_css
from proton.vpn.app.gtk.demo import discovery, launcher, registry
from proton.vpn.app.gtk.util import APPLICATION_ID


class DemoApp(Gtk.Application):
    """
    Renders one registered demo screen for visual checks, optionally saving a
    screenshot and exiting. See demo/launcher.py for the presentation logic.
    """

    def __init__(self):
        # NON_UNIQUE: demo runs shouldn't attach to (or block) an already
        # running instance of the app, or each other.
        super().__init__(
            application_id=APPLICATION_ID,
            flags=Gio.ApplicationFlags.NON_UNIQUE,
        )
        self.demo_screen: Optional[str] = None
        self.screenshot_path: Optional[str] = None
        self.add_options()

    def do_startup(self):  # pylint: disable=arguments-differ
        """Default GTK method.

        Loads the same CSS the production app uses, so demo screens are
        styled identically to what real users see.
        """
        Gtk.Application.do_startup(self)
        load_app_css(Gdk.Display.get_default())

    def do_activate(self):  # pylint: disable=arguments-differ
        """Default GTK method. Shows the requested demo screen."""
        launcher.show(self, self.demo_screen, screenshot_path=self.screenshot_path)

    def do_handle_local_options(self, options: GLib.VariantDict):  # noqa: E501 pylint: disable=arguments-differ
        """
        Handles the options defined in add_options.
        Returns:
            Any negative number: Start as usual
            Zero: Stop without error
            Any positive number: Stop with the number as error code
        """
        if options.contains("demo-list"):
            return self.handle_demo_list()

        demo = options.lookup_value("demo", GLib.VariantType.new("s"))
        if demo is not None:
            result = self.handle_demo(demo.get_string())
            if result != CONTINUE_STARTUP:
                return result
            screenshot = options.lookup_value("screenshot", GLib.VariantType.new("s"))
            if screenshot is not None:
                self.screenshot_path = screenshot.get_string()

        return CONTINUE_STARTUP

    def handle_demo_list(self) -> int:
        """
        Handles --demo-list option.
        Prints the registered demo screen names.
        """
        discovery.load_demo_screens()
        for name in registry.all_demo_screen_names():
            print(name)

        return EXIT_SUCCESS

    def handle_demo(self, screen_name: str) -> int:
        """
        Handles --demo option.
        Validate the requested demo screen and prepare for do_activate.
        """
        discovery.load_demo_screens()
        available_demo_screens = registry.all_demo_screen_names()
        if screen_name not in available_demo_screens:
            available = ", ".join(available_demo_screens)
            print(
                f"Unknown demo screen '{screen_name}'. Available: {available}",
                file=sys.stderr,
            )
            return EXIT_FAILURE

        self.demo_screen = screen_name
        return CONTINUE_STARTUP  # Continue startup; do_activate shows the demo screen.

    def add_options(self):
        """Adds the --demo, --demo-list and --screenshot command line options."""
        self.add_main_option(
            "demo",
            0,
            GLib.OptionFlags(0),
            GLib.OptionArg.STRING,
            "Render one demo screen for visual checks (use --demo-list for names)",
            "SCREEN"
        )

        self.add_main_option(
            "demo-list",
            0,
            GLib.OptionFlags(0),
            GLib.OptionArg.NONE,
            "List the available demo screen names and exit"
        )

        self.add_main_option(
            "screenshot",
            0,
            GLib.OptionFlags(0),
            GLib.OptionArg.STRING,
            "With --demo: save a PNG of the rendered screen to PATH and exit",
            "PATH"
        )
