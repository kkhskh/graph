"""Compatibility stub for legacy tests.

If the full implementation exists under *graph-heal/graph_heal/fault_injection.py*
we import and re-export its public symbols.  Otherwise we expose a very small
placeholder so that `import graph_heal.fault_injection` succeeds in CI.
"""

from __future__ import annotations

import importlib
import sys
from types import ModuleType
from typing import Any

_full_path = "graph_heal.graph_heal.fault_injection"  # nested copy bundled with research code

try:
    _mod: ModuleType = importlib.import_module(_full_path)
    # Re-export everything
    globals().update({k: v for k, v in _mod.__dict__.items() if not k.startswith("_")})
except ModuleNotFoundError:
    # Lightweight fallbacks -------------------------------------------------
    class FaultInjectionAPI:  # type: ignore
        def inject(self, *_, **__):  # noqa: D401
            return False

    class FaultInjector:  # type: ignore
        def __init__(self, *_, **__):
            pass

        def schedule(self, *_, **__):
            return False

    class ScheduledFaultInjector(FaultInjector):
        pass

    __all__ = [
        "FaultInjectionAPI",
        "FaultInjector",
        "ScheduledFaultInjector",
    ] 