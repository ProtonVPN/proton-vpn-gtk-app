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


Tests for the demo command-line surface: detection, the --demo / --demo-list
handlers, the not-available-in-build path, and demo-mode app flags.
"""
import sys
from unittest.mock import MagicMock, patch

import pytest
from gi.repository import Gio

from proton.vpn.app.gtk import app as app_module
from proton.vpn.app.gtk.app import App, demo_requested


@pytest.fixture
def demo_app():
    """An App built in demo mode (which skips startup logging / version listing)."""
    return App(controller=MagicMock(), is_demo=True)


@pytest.mark.parametrize("argv, expected", [
    (["app"], False),
    (["app", "--start-minimized"], False),
    (["app", "--demonstrate"], False),       # must not false-positive
    (["app", "--demo-list"], True),
    (["app", "--demo", "login"], True),
    (["app", "--demo=login"], True),
])
def test_demo_requested(argv, expected):
    assert demo_requested(argv) is expected


def test_load_demo_returns_the_demo_modules():
    loaded = App.load_demo()

    assert loaded is not None
    demo_registry, demo_launcher = loaded
    assert hasattr(demo_registry, "all_demo_screen_names")
    assert hasattr(demo_launcher, "build_window")


def test_load_demo_handles_a_build_without_the_demo_package(capsys):
    # In a shipped build the demo package is excluded; importing it must fail
    # gracefully rather than crash. Patching sys.modules is the only way to
    # simulate the package being absent.
    with patch.dict(sys.modules, {"proton.vpn.app.gtk.demo": None}):
        loaded = App.load_demo()

    assert loaded is None
    assert "not available" in capsys.readouterr().err


def test_handle_demo_accepts_a_known_screen(demo_app):
    result = demo_app.handle_demo("login")

    assert result == app_module.CONTINUE_STARTUP
    assert demo_app.demo_screen == "login"


def test_handle_demo_rejects_an_unknown_screen(demo_app, capsys):
    result = demo_app.handle_demo("does-not-exist")

    assert result == app_module.EXIT_FAILURE
    assert demo_app.demo_screen is None
    assert "Unknown demo screen" in capsys.readouterr().err


def test_handle_demo_list_prints_every_screen(demo_app, capsys):
    result = demo_app.handle_demo_list()

    assert result == app_module.EXIT_SUCCESS
    out = capsys.readouterr().out
    for name in ("nps-modal", "bug-report", "quick-connect", "login"):
        assert name in out


def test_demo_mode_is_non_unique():
    app = App(controller=MagicMock(), is_demo=True)

    assert app.get_flags() & Gio.ApplicationFlags.NON_UNIQUE


def test_normal_mode_is_not_non_unique():
    app = App(controller=MagicMock(), is_demo=False)

    assert not (app.get_flags() & Gio.ApplicationFlags.NON_UNIQUE)
