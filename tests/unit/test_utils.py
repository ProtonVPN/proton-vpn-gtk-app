from unittest.mock import Mock, call

from gi.repository import GLib

from proton.vpn.app.gtk.utils import glib
from proton.vpn.app.gtk.utils.search import normalize
from tests.unit.utils import process_gtk_events, run_main_loop


def test_run_once():
    mock = Mock()
    mock.return_value = True

    glib.run_once(mock, "arg1", "arg2")

    process_gtk_events()

    mock.assert_called_once_with("arg1", "arg2")


def test_run_periodically():
    main_loop = GLib.MainLoop()
    mock = Mock()

    glib.run_periodically(mock, "arg1", arg2="arg2", interval_ms=10)

    expected_number_of_calls = 3

    def stop_after_n_calls(*args, **kwargs):
        if mock.call_count == expected_number_of_calls:
            GLib.idle_add(main_loop.quit)

    mock.side_effect = stop_after_n_calls

    run_main_loop(main_loop)

    assert mock.call_count == expected_number_of_calls
    assert mock.mock_calls == [call("arg1", arg2="arg2") for _ in range(expected_number_of_calls)]


def test_normalize():
    input_string = "CH-PT#1 "
    normalized_string = normalize(input_string)
    assert normalized_string == "ch-pt#1"
