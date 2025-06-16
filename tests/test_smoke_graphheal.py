import importlib
import pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Dynamic import – prefer top-level package
GraphHeal = importlib.import_module("graph_heal.graph_heal").GraphHeal  # type: ignore[attr-defined]

def test_graphheal_flow():
    gh = GraphHeal()

    # Build a two-node service graph with a dependency
    gh.add_service("database")
    gh.add_service("api", dependencies=["database"])

    # Trigger anomalies by sending metrics above thresholds
    gh.update_metrics("database", {"cpu_usage": 90, "latency": 1500})
    gh.update_metrics("api", {"memory_usage": 95})

    # After anomaly handling the propagation history should not be empty
    assert gh.propagation_history, "Propagation history should record the anomalies"

    # And we can retrieve a health summary without crashing
    summary = gh.get_health_summary()
    assert isinstance(summary, dict) 