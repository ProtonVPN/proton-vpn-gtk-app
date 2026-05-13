"""
Copyright (c) 2026 Proton AG

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
import gc
import weakref

import pytest
from gi.repository import Gtk

from proton.vpn.app.gtk.utils.safe_signal_connect import safe_signal_connect


# Hosts with signal handlers defined —
# Each host subscribes its own bound methods to an
# external emitter via safe_signal_connect.


class _WidgetHost(Gtk.Box):
    """Widget host with the signal handler defined on it."""

    def __init__(self, emitter):
        super().__init__()
        self.calls = []
        self.handler_id = safe_signal_connect(
            emitter, "clicked", self._on_clicked
        )

    def _on_clicked(self, *args):
        self.calls.append(args)


class _PythonHost:
    """Non-widget Python host with the signal handler defined on it."""

    def __init__(self, emitter):
        self.calls = []
        safe_signal_connect(emitter, "clicked", self._on_clicked)

    def _on_clicked(self, *args):
        self.calls.append(args)


# --- bound-method (weak) path --------------------------------------------


def test_handler_fires_while_host_is_alive():
    emitter = Gtk.Button()
    host = _WidgetHost(emitter)

    emitter.emit("clicked")

    assert len(host.calls) == 1


def test_host_can_be_collected_when_dropped():
    """Ensure host is not leaked by connection to long lived signal emitter"""
    long_lived_emitter = Gtk.Button()
    host = _WidgetHost(long_lived_emitter)
    weak_host = weakref.ref(host)

    del host
    gc.collect()

    assert weak_host() is None


def test_handler_no_ops_after_host_collection():
    """Once the bound instance is collected, the wrapper sees a dead
    WeakMethod and silently does nothing"""
    long_lived_emitter = Gtk.Button()
    host = _WidgetHost(long_lived_emitter)

    del host
    gc.collect()

    long_lived_emitter.emit("clicked")  # must not raise


def test_returns_handler_id_usable_for_manual_disconnect():
    emitter = Gtk.Button()
    host = _WidgetHost(emitter)
    handler_id = host.handler_id

    assert emitter.handler_is_connected(handler_id)
    emitter.disconnect(handler_id)
    assert not emitter.handler_is_connected(handler_id)


# --- once=True (bound method) -------------------------------------------


class _OnceWidgetHost(Gtk.Box):
    """Widget host that connects to a signal that disconnects after firing once."""

    def __init__(self, emitter):
        super().__init__()
        self.calls = []
        self.handler_id = safe_signal_connect(
            emitter, "clicked", self._on_clicked, once=True
        )

    def _on_clicked(self, *args):
        self.calls.append(args)


def test_once_bound_method_disconnects_after_first_fire():
    emitter = Gtk.Button()
    host = _OnceWidgetHost(emitter)

    emitter.emit("clicked")

    assert not emitter.handler_is_connected(host.handler_id)
    assert len(host.calls) == 1


def test_once_bound_method_does_not_fire_a_second_time():
    emitter = Gtk.Button()
    host = _OnceWidgetHost(emitter)

    emitter.emit("clicked")
    emitter.emit("clicked")   # handler has self-disconnected

    assert len(host.calls) == 1


# --- free-function callable fixture --------------------------------------


class _Recorder:
    """Callable instance that records its calls. No ``__closure__`` and
    not a method, so ``safe_signal_connect`` accepts it via the
    free-function branch."""

    def __init__(self):
        self.calls = []

    def __call__(self, *args):
        self.calls.append(args)


@pytest.fixture
def recorder():
    return _Recorder()


# --- once=True (free function) ------------------------------------------


def test_once_free_function_disconnects_after_first_fire(recorder):
    emitter = Gtk.Button()

    handler_id = safe_signal_connect(emitter, "clicked", recorder, once=True)

    emitter.emit("clicked")

    assert not emitter.handler_is_connected(handler_id)
    assert len(recorder.calls) == 1


def test_once_free_function_does_not_fire_a_second_time(recorder):
    emitter = Gtk.Button()

    safe_signal_connect(emitter, "clicked", recorder, once=True)

    emitter.emit("clicked")
    emitter.emit("clicked")

    assert len(recorder.calls) == 1


# --- pure free function path ---------------------------------------------


def test_pure_free_function_is_accepted_and_fires(recorder):
    emitter = Gtk.Button()
    safe_signal_connect(emitter, "clicked", recorder)

    emitter.emit("clicked")

    assert len(recorder.calls) == 1


# --- rejection of unsupported callback types ----------------------------


def test_lambda_capturing_self_is_rejected():
    emitter = Gtk.Button()
    host = _WidgetHost(emitter)

    with pytest.raises(TypeError, match="closure-capturing"):
        safe_signal_connect(
            emitter, "clicked", lambda *_: host._on_clicked()
        )


def test_nested_function_with_captures_is_rejected():
    emitter = Gtk.Button()
    captured = []

    def closure_handler(*_):
        captured.append(True)

    with pytest.raises(TypeError, match="closure-capturing"):
        safe_signal_connect(emitter, "clicked", closure_handler)


def test_non_callable_is_rejected():
    emitter = Gtk.Button()

    with pytest.raises(TypeError, match="must be callable"):
        safe_signal_connect(emitter, "clicked", "not_a_function")


def test_destroy_signal_is_rejected_with_do_dispose_hint():
    """The 'destroy' rejection fires before any callback-type validation,
    so the callable passed doesn't matter — any valid callable triggers
    the same ValueError."""
    emitter = Gtk.Box()

    with pytest.raises(ValueError, match="do_dispose"):
        safe_signal_connect(emitter, "destroy", lambda *_: None)


# --- non-widget host -----------------------------------------------------


def test_non_widget_host_can_subscribe_with_bound_method():
    emitter = Gtk.Button()
    host = _PythonHost(emitter)

    emitter.emit("clicked")

    assert len(host.calls) == 1
