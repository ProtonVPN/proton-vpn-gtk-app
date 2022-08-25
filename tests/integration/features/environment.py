import logging
import os
from concurrent.futures import ThreadPoolExecutor
from threading import Thread, Event
from typing import Dict

from behave import fixture, use_fixture

from proton.vpn.app.gtk.app import App
from proton.vpn.core_api.api import ProtonVPNAPI

logging.basicConfig(level=logging.INFO)

os.environ["PROTON_API_ENVIRONMENT"] = "atlas"
VPNPLUS_USERNAME = "vpnplus"
VPNPLUS_PASSWORD = "12341234"


@fixture
def app(context):
    with ThreadPoolExecutor() as thread_pool_executor:
        app, app_thread, app_events = start_app(thread_pool_executor)
        context.app = app
        context.app_thread = app_thread
        context.app_events = app_events
        yield context
        stop_app(app, app_thread)


def start_app(thread_pool_executor) -> (App, Thread, Dict):
    app = App(thread_pool_executor)
    app_events = dict()

    # Register an event to be able to wait for the application to be ready.
    app_ready_event = Event()
    app.connect("app-ready", lambda *_: app_ready_event.set())
    app_events["app-ready"] = app_ready_event

    # Register an event to be able to wait for the server list to be ready.
    server_list_updated_event = Event()
    app.queue_signal_connect(
        "main_widget.vpn_widget.servers_widget::server-list-updated",
        lambda *_: server_list_updated_event.set()
    )
    app_events["server-list-updated"] = server_list_updated_event

    # Start the app in a thread.
    app_thread = Thread(target=app.run)
    app_thread.start()

    # Wait for the app to be ready.
    app_ready_event.wait(timeout=2)

    return app, app_thread, app_events


def stop_app(app: App, app_thread: Thread):
    if app.error_dialog:
        # Close error dialog when something went wrong.
        dialog_closed_event = Event()
        app.error_dialog.connect(
            "destroy-event",
            lambda *_: dialog_closed_event.set()
        )
        app.error_dialog.close()
        dialog_closed_event.wait(timeout=1)

    app.window.close()
    app_thread.join()


@fixture
def logged_in_session(context):
    context.api = ProtonVPNAPI()
    result = context.api.login(username=VPNPLUS_USERNAME, password=VPNPLUS_PASSWORD)
    assert result.success, f"Unable to login with {VPNPLUS_USERNAME}."
    yield context.api
    context.api.logout()


def before_scenario(context, scenario):
    if "not_implemented" in scenario.effective_tags:
        scenario.skip("Marked with @not_implemented")
        return

    use_fixture(app, context)


def after_scenario(context, scenario):
    if scenario.feature.name == "Login":
        ProtonVPNAPI().logout()


def before_feature(context, feature):
    if "not_implemented" in feature.tags:
        feature.skip("Marked with @not_implemented")
        return

    if feature.name == "Server List":
        use_fixture(logged_in_session, context)
