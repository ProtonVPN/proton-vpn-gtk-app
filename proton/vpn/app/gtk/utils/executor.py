"""
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
import asyncio
import concurrent
import functools
import inspect
from concurrent.futures import ThreadPoolExecutor
from threading import Thread
from typing import Optional, Coroutine, Callable, Union

from proton.vpn import logging

logger = logging.getLogger(__name__)


class AsyncExecutor:
    """
    Allows non-asyncio code to execute both coroutine functions and regular (blocking) functions
    in a non-blocking manner.

    Usage:

    .. code-block:: python
        import asyncio
        import time

        async def async_func(blocking_time: int) -> str:
            await asyncio.sleep(blocking_time)
            return "async func done"

        def regular_func(blocking_time: int) -> str:
            time.sleep(blocking_time)
            return "regular func done"

        with AsyncExecutor() as ce:
            future1 = ce.submit(async_func, blocking_time=0)
            future2 = ce.submit(regular_func, blocking_time=0)
            assert future1.result() == "async func done"
            assert future2.result() == "regular func done"

    """

    def __init__(
            self, loop: Optional[asyncio.AbstractEventLoop] = None,
            executor: Optional[ThreadPoolExecutor] = None
    ):
        self._thread: Optional[Thread] = None
        self._executor = executor or ThreadPoolExecutor()
        self._loop = loop or asyncio.new_event_loop()

    def start(self):
        """
        Starts the async executor.

        It starts a thread that runs the asyncio loop.
        """
        if self.is_running:
            raise RuntimeError("The executor is already running.")

        self._thread = Thread(target=self._run_asyncio_loop_forever, daemon=True)
        self._thread.start()

    @property
    def is_running(self) -> bool:
        """Returns True if the async executor has already been started and False otherwise."""
        return self._thread is not None

    def _run_asyncio_loop_forever(self):
        self._executor = ThreadPoolExecutor()
        self._loop.set_default_executor(self._executor)
        asyncio.set_event_loop(self._loop)
        try:
            self._loop.run_forever()
        finally:
            # Currently recommended way of shutting down the loop:
            # https://docs.python.org/3/library/asyncio-eventloop.html#asyncio.loop.close
            self._loop.run_until_complete(self._loop.shutdown_asyncgens())
            self._loop.run_until_complete(self._loop.shutdown_default_executor())
            self._loop.close()

    def stop(self):
        """
        Stops the async executor.

        It schedules a call to stop the asyncio loop and waits for the thread
        running it to stop.
        """
        if not self.is_running:
            logger.warning("The executor has already been stopped.")
            return

        self._loop.call_soon_threadsafe(self._loop.stop)
        self._thread.join()
        self._thread = None

    # pylint: disable=invalid-name
    def submit(self, fn: Union[Coroutine, Callable], *args, **kwargs) -> concurrent.futures.Future:
        """
        Submits a coroutine function or a callable to be run on the async executor
        in a thread-safe manner and non-blocking manner.

        :returns: a Future that can be waited for in a non-asyncio manner (or not).
        """
        if inspect.iscoroutinefunction(fn):
            coroutine = fn(*args, **kwargs)
            return asyncio.run_coroutine_threadsafe(coroutine, self._loop)

        return self._executor.submit(fn, *args, **kwargs)

    async def _blocking_function_to_coroutine(self, fn, *args, **kwargs):
        fn_wrapper = functools.partial(fn, *args, **kwargs)
        return await self._loop.run_in_executor(executor=None, func=fn_wrapper)

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
