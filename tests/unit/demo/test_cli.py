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


Tests for the demo command-line surface: DemoApp's --demo / --demo-list
handlers, and do_handle_local_options — the GLib option-parsing glue that
routes parsed CLI flags to those handlers.
"""
import pytest
from gi.repository import Gio, GLib

from proton.vpn.app.gtk.app import CONTINUE_STARTUP, EXIT_FAILURE, EXIT_SUCCESS
from proton.vpn.app.gtk.demo.demo_app import DemoApp


@pytest.fixture
def demo_app():
    """A DemoApp, ready to handle --demo / --demo-list."""
    return DemoApp()


def _options(flags):
    """A GLib.VariantDict populated the way GLib's own parser would from CLI flags."""
    variant_dict = GLib.VariantDict.new()
    for name, value in flags.items():
        if isinstance(value, bool):
            variant_dict.insert_value(name, GLib.Variant.new_boolean(value))
        else:
            variant_dict.insert_value(name, GLib.Variant.new_string(value))
    return variant_dict


def test_handle_demo_accepts_a_known_screen(demo_app):  # pylint: disable=redefined-outer-name
    result = demo_app.handle_demo("login")

    assert result == CONTINUE_STARTUP
    assert demo_app.demo_screen == "login"


# pylint: disable-next=redefined-outer-name
def test_handle_demo_rejects_an_unknown_screen(demo_app, capsys):
    result = demo_app.handle_demo("does-not-exist")

    assert result == EXIT_FAILURE
    assert demo_app.demo_screen is None
    assert "Unknown demo screen" in capsys.readouterr().err


# pylint: disable-next=redefined-outer-name
def test_handle_demo_list_prints_every_screen(demo_app, capsys):
    result = demo_app.handle_demo_list()

    assert result == EXIT_SUCCESS
    out = capsys.readouterr().out
    for name in ("nps-modal", "bug-report", "quick-connect", "login"):
        assert name in out


def test_demo_app_is_non_unique(demo_app):  # pylint: disable=redefined-outer-name
    assert demo_app.get_flags() & Gio.ApplicationFlags.NON_UNIQUE


@pytest.mark.parametrize("flags, expected_screen, expected_screenshot_path", [
    ({"demo": "login", "screenshot": "/tmp/x.png"}, "login", "/tmp/x.png"),
    ({"demo": "login"}, "login", None),
    ({}, None, None),
])
def test_do_handle_local_options_sets_state_and_continues_startup(
    # pylint: disable-next=redefined-outer-name
    demo_app, flags, expected_screen, expected_screenshot_path
):
    result = demo_app.do_handle_local_options(_options(flags))

    assert result == CONTINUE_STARTUP
    assert demo_app.demo_screen == expected_screen
    assert demo_app.screenshot_path == expected_screenshot_path


# pylint: disable-next=redefined-outer-name
def test_do_handle_local_options_propagates_an_unknown_screen_failure(demo_app, capsys):
    result = demo_app.do_handle_local_options(_options({"demo": "does-not-exist"}))

    assert result == EXIT_FAILURE
    assert "Unknown demo screen" in capsys.readouterr().err


# pylint: disable-next=redefined-outer-name
def test_do_handle_local_options_routes_demo_list(demo_app, capsys):
    result = demo_app.do_handle_local_options(_options({"demo-list": True}))

    assert result == EXIT_SUCCESS
