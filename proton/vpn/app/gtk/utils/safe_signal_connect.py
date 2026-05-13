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


Memory-safe GObject signal connections.

Connects callbacks to GObject signals while statically rejecting any
use that could leak. Two callback types are valid:

1. Bound methods (``self.on_clicked``). The bound instance is held
   weakly via ``weakref.WeakMethod``, so the signal connection alone
   cannot keep the bound instance alive.

2. Pure free functions (``__closure__`` is empty). They reference
   nothing about any instance — no leak is possible. They are
   connected directly without WeakMethod.

Anything else is rejected at connection time:

- Closure-capturing callables (lambdas, nested functions with captures,
  ``functools.partial`` over a bound method, etc.) — closure cells hold
  their captures strongly and may leak whatever they reference. Raises
  ``TypeError``.
- The ``"destroy"`` signal is rejected explicitly. By the time destroy
  fires from inside ``pygobject_dealloc`` the wrapper's weakrefs have
  already been cleared and the handler is silently skipped. Override
  ``do_dispose`` instead. Raises ``ValueError``.

The signature is fixed at three positional arguments — extra
``user_data`` forwarded to the handler (the GObject ``connect`` idiom)
is not supported. If you need to dispatch extra context, store it on
``self`` and read it inside the bound method.

A keyword-only ``once=True`` flag connects a one-shot handler that
self-disconnects from *emitter* after firing once, or after the bound
instance is collected — whichever comes first. The same callback
restrictions apply.

Usage::

    safe_signal_connect(button, "clicked", self.on_clicked)              # bound method
    safe_signal_connect(button, "clicked", log_click)                    # pure free function
    safe_signal_connect(button, "clicked", self.on_clicked, once=True)   # one-shot
"""
import inspect
import types
import weakref
from typing import Callable

from gi.repository import GObject

from proton.vpn import logging

logger = logging.getLogger(__name__)


def safe_signal_connect(
    emitter: GObject.Object,
    signal: str,
    callback: Callable,
    *,
    once=False
) -> int:
    """Connect *callback* to *emitter*'s *signal*.

    Bound methods are held weakly via ``WeakMethod``; pure free functions
    (no closure captures) are connected directly. Closure-capturing
    callables raise ``TypeError``. The ``"destroy"`` signal raises
    ``ValueError`` (override ``do_dispose`` instead).

    If *once* is True, the handler self-disconnects from *emitter* after
    firing once (or after the bound instance is collected, whichever
    comes first).

    Returns the GObject handler id so the caller can disconnect manually
    if needed."""
    if signal == "destroy":
        raise ValueError(
            "safe_signal_connect cannot wrap the 'destroy' signal: by the "
            "time destroy fires from inside pygobject_dealloc, the wrapper's "
            "weakrefs have already been cleared and WeakMethod() returns "
            "None, so the handler is silently skipped. Override do_dispose "
            "instead:\n"
            "    def do_dispose(self):\n"
            "        # ...your cleanup here, idempotent...\n"
            "        SuperClass.do_dispose(self)  # e.g. Gtk.Box.do_dispose"
        )

    if inspect.ismethod(callback):
        return _connect_weak(emitter, signal, callback, once=once)

    if not callable(callback):
        raise TypeError(
            f"safe_signal_connect callback must be callable, got "
            f"{type(callback).__name__}."
        )

    if _has_closure_captures(callback):
        raise TypeError(
            "safe_signal_connect rejects closure-capturing callbacks "
            "(lambdas, nested functions with captures): closure cells hold "
            "their captures strongly and may leak. Pass a bound method, or "
            "a pure free function with no closure captures."
        )

    return _connect(emitter, signal, callback, once=once)


def _has_closure_captures(callback: Callable) -> bool:
    """True if *callback* is a function-like with non-empty closure cells."""
    return bool(getattr(callback, "__closure__", None))


def _connect_weak(
    emitter: GObject.Object,
    signal: str,
    method: types.MethodType,
    *,
    once: bool = False,
) -> int:
    """Connect via ``weakref.WeakMethod`` so the handler does not extend
    the bound instance's lifetime. The wrapper transparently dispatches
    to the live bound method; once the instance is collected, the wrapper
    no-ops and the slot stays inert in *emitter*'s signal table until
    *emitter* itself is destroyed.

    If ``once=True``, the wrapper self-disconnects from *emitter* after
    firing once."""
    weak_method = weakref.WeakMethod(method)
    weak_emitter = weakref.ref(emitter)
    handler_id = None

    # Captured as plain strings so the wrapper closure holds no strong
    # reference to emitter or the bound instance.
    receiver_repr = (
        f"{type(method.__self__).__name__}.{method.__func__.__name__}"
    )
    emitter_repr = f"{type(emitter).__name__}@{hex(id(emitter))}"

    def wrapper(*args):
        if once and handler_id is not None:
            live_emitter = weak_emitter()
            if live_emitter is not None:
                live_emitter.disconnect(handler_id)

        target = weak_method()
        if target is not None:
            return target(*args)

        logger.warning(
            "Signal smell: '%s' fired on %s but receiver %s was already "
            "collected — handler no-op'd. The signal connection outlived its listener",
            signal, emitter_repr, receiver_repr,
        )
        return None

    handler_id = emitter.connect(signal, wrapper)
    return handler_id


def _connect(
    emitter: GObject.Object,
    signal: str,
    callback: Callable,
    *,
    once: bool = False,
) -> int:
    """Connect a pure free function (no closure captures). For persistent
    connections this delegates directly to ``emitter.connect``. With
    ``once=True``, a small self-disconnecting wrapper is used."""
    if not once:
        return emitter.connect(signal, callback)

    weak_emitter = weakref.ref(emitter)
    handler_id = None

    def wrapper(*args):
        if handler_id is not None:
            live_emitter = weak_emitter()
            if live_emitter is not None:
                live_emitter.disconnect(handler_id)

        callback(*args)

    handler_id = emitter.connect(signal, wrapper)
    return handler_id
