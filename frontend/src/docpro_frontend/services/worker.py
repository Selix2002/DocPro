from collections.abc import Callable
from typing import Any

from PySide6.QtCore import QObject, QRunnable, Signal

# Keeps Python references alive until each worker finishes running, preventing
# the double-free that occurs when Qt's autoDelete tries to free an object
# that Python's GC already destroyed (or vice-versa).
_active: set["Worker"] = set()


class _Signals(QObject):
    result = Signal(object)
    error = Signal(str)


class Worker(QRunnable):
    """Generic thread-pool worker. Runs fn() off the main thread and emits
    result/error signals back on the main thread via Qt's signal mechanism."""

    def __init__(self, fn: Callable[[], Any]) -> None:
        super().__init__()
        self.setAutoDelete(False)
        self.fn = fn
        self.signals = _Signals()
        _active.add(self)

    def run(self) -> None:
        try:
            self.signals.result.emit(self.fn())
        except Exception as exc:
            self.signals.error.emit(str(exc))
        finally:
            _active.discard(self)
