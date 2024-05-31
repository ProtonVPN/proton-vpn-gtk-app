import time
from unittest.mock import Mock

from proton.vpn.app.gtk.utils.scheduler import Scheduler


def test_start_schedules_call_to_run_tasks_to_fire():
    glib_mock = Mock()
    scheduler = Scheduler(glib=glib_mock)

    scheduler.start()

    glib_mock.timeout_add_seconds.assert_called_once_with(0, scheduler.run_tasks_ready_to_fire)


def test_run_tasks_ready_to_fire_schedules_another_call_to_itself():
    glib_mock = Mock()
    scheduler = Scheduler(glib=glib_mock)

    scheduler.run_tasks_ready_to_fire()

    glib_mock.timeout_add_seconds.assert_called_once()
    assert glib_mock.timeout_add_seconds.call_args[0][1] == scheduler.run_tasks_ready_to_fire


def test_run_task_ready_to_fire_only_runs_tasks_with_expired_timestamps():
    glib_mock = Mock()
    scheduler = Scheduler(glib=glib_mock)

    scheduler.run_after(delay_in_seconds=0, task=Mock())  # should run since the delay is 0 seconds.
    second_task_id = scheduler.run_after(delay_in_seconds=30, task=Mock())  # should not run yet since the delay is 30 seconds.

    scheduler.run_tasks_ready_to_fire()

    assert scheduler.get_next_task().id == second_task_id


def test_stop_unschedules_call_to_run_tasks_ready_to_fire():
    glib_mock = Mock()
    scheduler = Scheduler(glib=glib_mock)
    scheduler.start()

    scheduler.stop()

    glib_mock.source_remove.assert_called_once_with(
        glib_mock.timeout_add_seconds.return_value
    )


def test_run_at_schedules_new_task():
    scheduler = Scheduler(glib=Mock())

    task_id = scheduler.run_at(timestamp=time.time() + 10, task=Mock())

    scheduler.get_next_task().id == task_id


def test_cancel_task_removes_task_from_task_list():
    scheduler = Scheduler(glib=Mock())
    task_id = scheduler.run_after(0, Mock())

    scheduler.cancel_task(task_id)

    assert scheduler.number_of_remaining_tasks == 0
