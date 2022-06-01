from concurrent.futures import ThreadPoolExecutor

from proton.vpn.app.gtk.controller import Controller


class App:
    """Application entry point."""

    def __init__(self, thread_pool_executor: ThreadPoolExecutor):
        self._controller = Controller(thread_pool_executor=thread_pool_executor)

    def run(self):
        return self._controller.run()
