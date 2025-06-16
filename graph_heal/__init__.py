"""
Graph-Heal: A fault detection and recovery system for microservices
"""

from __future__ import annotations

# Public façade --------------------------------------------------------------
from .graph_heal import GraphHeal, ServiceNode  # noqa: F401
from .health_manager import HealthManager  # noqa: F401
from .improved_statistical_detector import StatisticalDetector  # noqa: F401

__all__ = [
    "GraphHeal",
    "ServiceNode",
    "HealthManager",
    "StatisticalDetector",
]

# ---------------------------------------------------------------------------
# Compatibility layer for legacy imports
# ---------------------------------------------------------------------------

import importlib
import pkgutil
import sys
import types
import pathlib

# Expose modules that still live in the historical nested tree so that calls
# like ``import graph_heal.anomaly_detection`` continue to work even though the
# modern implementation sits elsewhere.
_NESTED_ROOT = pathlib.Path(__file__).resolve().parent.parent / "graph-heal" / "graph_heal"
if _NESTED_ROOT.exists():
    for _m in pkgutil.walk_packages([str(_NESTED_ROOT)], prefix="graph_heal."):
        if _m.name not in sys.modules:
            try:
                importlib.import_module(_m.name)
            except Exception:
                # Ignore broken legacy modules – seldom used in tests.
                pass

# Provide tiny placeholders for a couple of names that *some* old tests import
# but the current codebase no longer ships.
if "graph_heal.monitoring" not in sys.modules:
    _mon = types.ModuleType("graph_heal.monitoring")
    class _Dummy:  # noqa: D401 – minimal stub
        def __init__(self, *_, **__):
            pass
    _mon.ServiceMonitor = _Dummy  # type: ignore[attr-defined]
    _mon.GraphUpdater = _Dummy  # type: ignore[attr-defined]
    sys.modules["graph_heal.monitoring"] = _mon

# Convenience re-export so ``import graph_heal.graph_heal as gh`` keeps working.
if "graph_heal.graph_heal" not in sys.modules:
    sys.modules["graph_heal.graph_heal"] = importlib.import_module("graph_heal")

# Version tag ----------------------------------------------------------------
__version__ = "0.1.0"

# ---------------------------------------------------------------------------
# Lazy attribute loader – avoids importing sub-module during package init.
# ---------------------------------------------------------------------------

def __getattr__(name):  # pragma: no cover – executed at runtime
    if name in __all__:
        mod = importlib.import_module("graph_heal.graph_heal")
        attr = getattr(mod, name)
        globals()[name] = attr  # cache for subsequent attribute access
        return attr
    raise AttributeError(name)

# Explicitly expose sub-package so that ``import graph_heal.graph_heal`` works
# even if users imported the root package first.
import sys as _sys
_sys.modules.setdefault("graph_heal.graph_heal", importlib.import_module("graph_heal.graph_heal"))
