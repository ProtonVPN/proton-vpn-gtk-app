from concurrent.futures import ThreadPoolExecutor

from proton.vpn.app.gtk.controller import Controller
from proton.vpn.app.gtk.view import View


class App:
    """Application entry point."""

    def __init__(self, thread_pool_executor: ThreadPoolExecutor):
        controller = Controller(
            thread_pool_executor=thread_pool_executor
        )
        self._view = View(controller=controller)

    def run(self):
        return self._view.run()
