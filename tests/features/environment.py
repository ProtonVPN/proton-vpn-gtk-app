import logging
from concurrent.futures import ThreadPoolExecutor
from threading import Thread, Event

from behave import fixture, use_fixture

from proton.vpn.app.gtk.app import App

logging.basicConfig(level=logging.INFO)


@fixture
def app(context):
    with ThreadPoolExecutor() as thread_pool_executor:
        context.app = App(thread_pool_executor)
        window_added_event = Event()
        context.app.connect("window-added", lambda *_: window_added_event.set())
        context.app_thread = Thread(target=context.app.run)
        context.app_thread.start()
        window_added_event.wait(timeout=2)
        yield context.app
        context.app.window.close()
        context.app_thread.join()


def before_scenario(context, scenario):
    use_fixture(app, context)
