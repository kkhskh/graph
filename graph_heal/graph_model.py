"""Shim for legacy imports of graph_heal.graph_model."""
from __future__ import annotations
import importlib, types

_full = "graph_heal.graph_heal.graph_model"
try:
    _m = importlib.import_module(_full)
    globals().update({k: v for k, v in _m.__dict__.items() if not k.startswith("_")})
except ModuleNotFoundError:  # pragma: no cover
    class GraphModel:  # type: ignore
        def __init__(self, *_, **__):
            pass

    def create_sample_graph():  # type: ignore
        return {}

    __all__ = ["GraphModel", "create_sample_graph"] 