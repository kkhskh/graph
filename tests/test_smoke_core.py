from unittest.mock import MagicMock
import importlib

# Prefer top-level implementation; fall back otherwise
try:
    ServiceGraph = importlib.import_module("graph_heal.service_graph").ServiceGraph  # type: ignore[attr-defined]
except ModuleNotFoundError:
    ServiceGraph = importlib.import_module("graph_heal.graph_analysis").ServiceGraph  # type: ignore[attr-defined]

from graph_heal.anomaly_detection import StatisticalAnomalyDetector
from graph_heal.recovery_system import EnhancedRecoverySystem, RecoveryActionType


def test_core_execution():
    """Run a mini end-to-end flow that exercises the main subsystems."""

    sg = ServiceGraph()
    sg.add_service("frontend")
    sg.add_service("backend")
    sg.add_dependency("frontend", "backend")

    # Anomaly Detection – feed a clear spike
    det = StatisticalAnomalyDetector(window_size=3, z_score_threshold=1.0)
    for cpu in (1, 2, 50):  # ensure non-zero variance so spike triggers anomaly
        det.detect_anomalies({"frontend": {"metrics": {"cpu": cpu}}})

    # Recovery – create & execute a restart action
    ers = EnhancedRecoverySystem(sg, MagicMock())
    action = ers.create_recovery_action("frontend", RecoveryActionType.RESTART)
    ers.execute_recovery_action(action)

    # Feed metrics history to compute health and correlation
    from datetime import datetime, timedelta

    now = datetime.utcnow()
    for i, cpu in enumerate((10, 20, 30, 40, 50)):
        sg.add_metrics("frontend", {"service_cpu_usage": cpu}, now + timedelta(seconds=i))
        sg.add_metrics("backend", {"service_cpu_usage": cpu * 0.8}, now + timedelta(seconds=i))

    health_front = sg.score_node_health("frontend")
    strength = sg.dependency_strength("frontend", "backend")

    # Assertions – graph populated and anomaly recorded
    assert det.get_all_anomalies(), "Expected at least one anomaly to be recorded"
    assert 0 < health_front <= 1.0
    assert 0 < strength <= 1.0 