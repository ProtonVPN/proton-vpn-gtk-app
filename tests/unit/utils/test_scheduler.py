import time
from unittest.mock import Mock

from gi.repository import GLib

from proton.vpn.app.gtk.utils.scheduler import Scheduler
from tests.unit.testing_utils import run_main_loop


def test_start_runs_tasks_ready_to_fire_periodically():
    scheduler = Scheduler(check_interval_in_ms=10)

    main_loop = GLib.MainLoop()

    task_1 = Mock()
    scheduler.run_after(0, task_1)

    task_2 = Mock()
    def task2_wrapper():
        task_2()
        main_loop.quit()

    in_100_ms = time.time() + 0.1
    scheduler.run_at(in_100_ms, task2_wrapper)

    scheduler.start()

    run_main_loop(main_loop, timeout_in_ms=10000)

    task_1.assert_called_once()
    task_2.assert_called_once()
    assert len(scheduler.task_list) == 0


def test_run_task_ready_to_fire_only_runs_tasks_with_expired_timestamps():
    glib_mock = Mock()
    scheduler = Scheduler(glib=glib_mock)

    scheduler.run_after(delay_in_seconds=0, task=Mock())  # should run since the delay is 0 seconds.
    second_task_id = scheduler.run_after(delay_in_seconds=30, task=Mock())  # should not run yet since the delay is 30 seconds.

    scheduler.run_tasks_ready_to_fire()

    assert scheduler.task_list[0].id == second_task_id


def test_stop_unschedules_call_to_run_tasks_ready_to_fire():
    glib_mock = Mock()
    scheduler = Scheduler(glib=glib_mock)
    scheduler.start()

    scheduler.stop()

    glib_mock.source_remove.assert_called_once_with(
        glib_mock.timeout_add.return_value
    )


def test_run_at_schedules_new_task():
    scheduler = Scheduler(glib=Mock())

    task_id = scheduler.run_at(timestamp=time.time() + 10, task=Mock())

    scheduler.task_list[0].id == task_id


def test_cancel_task_removes_task_from_task_list():
    scheduler = Scheduler(glib=Mock())
    task_id = scheduler.run_after(0, Mock())

    scheduler.cancel_task(task_id)

    assert scheduler.number_of_remaining_tasks == 0
