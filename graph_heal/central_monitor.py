"""Central monitoring stub for unit tests."""
from __future__ import annotations

class CentralMonitor:  # type: ignore
    def __init__(self, *_, **__):
        self.records = []

    def record(self, entry):
        self.records.append(entry)

    def latest(self):
        return self.records[-1] if self.records else None

    # ------------------------------------------------------------------
    # Legacy API shim ---------------------------------------------------
    # ------------------------------------------------------------------
    def start_monitoring(self):  # noqa: D401
        """Begin monitoring – legacy stub.

        The historical implementation spun up background tasks. For unit tests
        we only need the symbol to exist and be callable, so we simply return
        True to indicate that the request was *accepted*.
        """
        return True

    def stop_monitoring(self):  # noqa: D401
        """Terminate monitoring – legacy stub counterpart of *start_monitoring*."""
        return True

__all__ = ["CentralMonitor"] 