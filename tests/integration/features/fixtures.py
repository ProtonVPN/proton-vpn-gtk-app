"""
Shared fixtures across all features.

Fixtures that are scoped to a single feature go in their own module (in /steps).
"""
from concurrent.futures import ThreadPoolExecutor
from threading import Thread, Event
from typing import Dict
from unittest.mock import Mock

from behave import fixture, use_fixture

from proton.vpn.app.gtk.app import App
from proton.vpn.core_api.session import ClientTypeMetadata
from proton.vpn.app.gtk.controller import Controller
from proton.vpn.app.gtk.services import VPNReconnector


def before_each_scenario(context, scenario):
    """Called before running each scenario of each feature from environment.py."""
    use_fixture(app, context)


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
    app = App(
        thread_pool_executor,
        controller=Controller(
            thread_pool_executor,
            vpn_reconnector=Mock(VPNReconnector))
    )
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
