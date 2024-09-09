"""
Copyright (c) 2024 Proton AG

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
import time

from dataclasses import dataclass
from types import ModuleType
from typing import Callable, Optional

from gi.repository import GLib


@dataclass
class TaskRecord:
    """Record with details of the task to be executed and when."""
    id: int  # pylint: disable=invalid-name
    timestamp: float
    callable: Callable


class Scheduler:
    """
    Task scheduler.

    The goal of this implementation is to improve the accuracy of the built-in scheduler
    when the system is suspended/resumed. The built-in scheduler does not take into account
    the time the system has been suspended after a task has been scheduled to run after a
    certain amount of time. In this case, the clock is paused and then resumed.

    The way this implementation workarounds this issue is by keeping a redord of tasks to
    be executed and the timestamp at which they should be executed. Then it periodically
    checks the lists for any tasks that should be executed and runs them.
    """

    def __init__(self, glib: ModuleType = GLib, check_interval_in_ms: int = 10_000):
        self.check_interval_in_ms = check_interval_in_ms
        self._last_task_id: int = 0
        self._task_list = []
        self._scheduler_handler_id: Optional[int] = None
        self._glib = glib

    @property
    def task_list(self):
        """Returns the list of tasks currently scheduled."""
        return self._task_list

    @property
    def is_started(self):
        """Returns whether the scheduler has been started or not."""
        return self._scheduler_handler_id is not None

    @property
    def number_of_remaining_tasks(self):
        """Returns the number of remaining tasks to be executed."""
        return len(self._task_list)

    def get_tasks_ready_to_fire(self):
        """
        Returns the tasks that are ready to fire, that is the tasks with a timestamp lower or
        equal than the current unix time."""
        now = time.time()
        return list(filter(lambda task: task.timestamp <= now, self._task_list))

    def start(self):
        """Starts the scheduler."""
        if self.is_started:
            raise RuntimeError("Scheduler was already started.")

        self._schedule_periodic_task_list_check()

    def stop(self):
        """Stops the scheduler and discards all remaining tasks."""
        self._cancel_periodic_task_list_check()
        self._task_list = []

    def run_after(self, delay_in_seconds: float, task: Callable, *args, **kwargs):
        """
        Runs the task specified after a delay specified in seconds.
        :returns: the scheduled task id.
        """
        return self.run_at(time.time() + delay_in_seconds, task, *args, **kwargs)

    def run_at(self, timestamp: float, task: Callable, *args, **kwargs) -> int:
        """
        Runs the task at the specified timestamp.
        :returns: the scheduled task id.
        """
        def wrapper():
            task(*args, **kwargs)
            return GLib.SOURCE_REMOVE

        self._last_task_id += 1

        record = TaskRecord(id=self._last_task_id, timestamp=timestamp, callable=wrapper)
        self._task_list.append(record)

        return record.id

    def cancel_task(self, task_id):
        """Cancels a task to be executed given its task id."""
        for task in self._task_list:
            if task.id == task_id:
                self._task_list.remove(task)
                break

    def _cancel_periodic_task_list_check(self):
        if self.is_started:
            self._glib.source_remove(self._scheduler_handler_id)
            self._scheduler_handler_id = None

    def _schedule_periodic_task_list_check(self):
        # Run the tasks ready to be executed immediately.
        self._glib.idle_add(self.run_tasks_ready_to_fire)
        # Schedule the next periodic checks (the first one happens at the end of the interval)
        self._scheduler_handler_id = self._glib.timeout_add(
            self.check_interval_in_ms,
            self._run_tasks_ready_to_fire_periodically
        )

    def run_tasks_ready_to_fire(self):
        """
        Runs the tasks ready to be executed, that is the tasks with a timestamp lower or equal
        than the current unix time, and removes them from the list.
        """
        tasks_ready_to_fire = self.get_tasks_ready_to_fire()

        # Run the tasks that are ready to be run.
        for task in tasks_ready_to_fire:
            self._glib.idle_add(task.callable)

        # Discard the tasks that have been run.
        for task in tasks_ready_to_fire:
            self._task_list.remove(task)

    def _run_tasks_ready_to_fire_periodically(self):
        self.run_tasks_ready_to_fire()
        return GLib.SOURCE_CONTINUE
