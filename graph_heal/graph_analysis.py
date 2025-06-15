from __future__ import annotations

"""Shim module exposing ServiceGraph under *graph_heal.graph_analysis*.

Several legacy tests import ServiceGraph from this module.  To avoid code
duplication we simply re-export the real implementation from
:pyfile:`graph_heal.service_graph`.
"""

try:
    from graph_heal.service_graph import ServiceGraph  # noqa: F401
except Exception:  # pragma: no cover – fallback if heavy deps missing
    class ServiceGraph:  # type: ignore
        """Fallback dummy so imports in tests don't crash when deps absent."""

        def __init__(self, *_, **__):
            pass 