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
import time

from proton.vpn.app.gtk.utils.executor import AsyncExecutor


def test_async_executor_submit_with_coroutine_func():
    async def asyncio_func(blocking_time):
        await asyncio.sleep(blocking_time)
        return "done"

    with AsyncExecutor() as executor:
        future = executor.submit(asyncio_func, blocking_time=0)
        assert future.result() == "done"


def test_async_executor_submit_regular_func():
    def blocking_func(blocking_time):
        time.sleep(blocking_time)
        return "done"

    with AsyncExecutor() as executor:
        future = executor.submit(blocking_func, blocking_time=0)
        assert future.result() == "done"


def test_async_executor_start_starts_running_the_executor():
    executor = AsyncExecutor()
    executor.start()
    assert executor.is_running


def test_async_executor_stop_stops_running_the_executor():
    executor = AsyncExecutor()
    executor.start()
    executor.stop()
    assert not executor.is_running
