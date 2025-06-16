import pytest
import prometheus_client
import sys, pathlib
import importlib

# Ensure workspace root is at the front of sys.path so `graph_heal.*` resolves
root_dir = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(root_dir))

@pytest.fixture(autouse=True)
def _no_prometheus_bind(monkeypatch):
    """Prevent Prometheus from trying to bind ports during unit tests."""
    monkeypatch.setattr(prometheus_client, "start_http_server", lambda *a, **k: None)

_mod = importlib.import_module("graph_heal.graph_heal")
print(
    f"[DEBUG] graph_heal.graph_heal loaded from: {_mod.__file__} | has update_metrics: {hasattr(_mod.GraphHeal, 'update_metrics')}",
    file=sys.stderr,
) 