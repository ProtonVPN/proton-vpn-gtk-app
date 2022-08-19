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
        app_ready_event = Event()
        context.app.connect("app-ready", lambda *_: app_ready_event.set())
        context.app_thread = Thread(target=context.app.run)
        context.app_thread.start()
        app_ready_event.wait(timeout=2)
        yield context.app

        if context.app.error_dialog:
            dialog_closed_event = Event()
            context.app.error_dialog.connect(
                "destroy-event",
                lambda *_: dialog_closed_event.set()
            )
            context.app.error_dialog.close()
            dialog_closed_event.wait(timeout=1)

        context.app.window.close()
        context.app_thread.join()


def before_scenario(context, scenario):
    if "not_implemented" in scenario.effective_tags:
        scenario.skip("Marked with @not_implemented")
        return

    use_fixture(app, context)


def before_feature(context, feature):
    if "not_implemented" in feature.tags:
        feature.skip("Marked with @not_implemented")
        return
