"""
Shared fixtures across all features.

Fixtures that are scoped to a single feature go in their own module (in /steps).


Copyright (c) 2023 Proton AG

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
"""
import os
from concurrent.futures import ThreadPoolExecutor
from threading import Thread, Event
from typing import Dict
from unittest.mock import Mock

from behave import fixture, use_fixture

from proton.vpn.app.gtk.app import App
from proton.vpn.app.gtk.controller import Controller
from proton.vpn.app.gtk.services import VPNReconnector
from proton.vpn.app.gtk.utils.executor import AsyncExecutor
from tests.integration.features.atlas_utils import AtlasUsers


def configure_atlas_environment():
    current_env = os.environ.get("PROTON_API_ENVIRONMENT")
    if not current_env:
        current_env = "atlas"
        os.environ["PROTON_API_ENVIRONMENT"] = "atlas"
    if not current_env.startswith("atlas"):
        raise RuntimeError(f"Unexpected PROTON_API_ENVIRONMENT env var: {current_env}")


def create_atlas_users(context):
    print("Creating atlas users...")
    atlas_users = AtlasUsers()
    context.atlas_users = atlas_users

    user = atlas_users.create()
    print(f"{user=}")
    context.free_user_id = user["Dec_ID"]
    context.free_user_name = user["Name"]
    context.free_user_password = user["Password"]

    secret = "A" * 32
    two_factor_auth_user = atlas_users.create(two_factor_auth_secret=secret)
    print(f"{two_factor_auth_user=}")
    context.two_factor_user_id = two_factor_auth_user["Dec_ID"]
    context.two_factor_user_name = two_factor_auth_user["Name"]
    context.two_factor_user_password = two_factor_auth_user["Password"]
    context.two_factor_user_2fa_secret = secret
    print("Atlas users created.")


def delete_atlas_users(context):
    print("Deleting atlas users...")
    context.atlas_users.cleanup()
    print("Atlas users deleted.")


def before_each_scenario(context, scenario):
    """Called before running each scenario of each feature from environment.py."""
    use_fixture(app, context)


@fixture
def app(context):
    with AsyncExecutor() as executor:
        app, app_thread, app_events = start_app(executor)
        context.app = app
        context.app_thread = app_thread
        context.app_events = app_events
        yield context
        stop_app(app, app_thread)


def start_app(async_executor) -> (App, Thread, Dict):
    controller = Controller.get(async_executor)
    app = App(controller)
    app_events = dict()

    # Register an event to be able to wait for the application to be ready.
    app_ready_event = Event()
    app.connect("app-ready", lambda *_: app_ready_event.set())
    app_events["app-ready"] = app_ready_event

    # Register an event to be able to wait for the server list to be ready.
    server_list_updated_event = Event()
    app.queue_signal_connect(
        "main_widget.vpn_widget::vpn-widget-ready",
        lambda *_: server_list_updated_event.set()
    )
    app_events["vpn-widget-ready"] = server_list_updated_event

    # Start the app in a thread.
    app_thread = Thread(target=app.run)
    app_thread.start()

    # Wait for the app to be ready.
    app_ready_event.wait(timeout=2)

    return app, app_thread, app_events


def stop_app(app: App, app_thread: Thread):
    # Close error dialog when something went wrong.
    if app.error_dialog:
        dialog_closed_event = Event()
        app.error_dialog.connect(
            "response",
            lambda *_: dialog_closed_event.set()
        )
        app.error_dialog.close()
        dialog_closed = dialog_closed_event.wait(timeout=1)
        assert dialog_closed, "Error dialog could not be closed."

    app.quit_safely()
    app_thread.join()
