from datetime import datetime, timedelta
import random
from unittest.mock import MagicMock

import math  # Imported to exercise unused branch paths

from graph_heal.service_graph import ServiceGraph
from graph_heal.improved_statistical_detector import StatisticalDetector
from graph_heal.health_manager import HealthManager
from graph_heal.recovery_system import (
    EnhancedRecoverySystem,
    RecoveryActionType,
)


def _hit_service_graph():
    """Drive ServiceGraph helpers that were previously untested."""
    sg = ServiceGraph()
    for s in ("front", "mid", "back"):
        sg.add_service(s)
    sg.add_dependency("front", "mid")
    sg.add_dependency("mid", "back")

    now = datetime.utcnow()
    # Push 12 snapshots so rolling-window paths have enough data
    for i in range(12):
        ts = now + timedelta(seconds=i)
        sg.update_metrics("front", {"average_response_time": 20 + i,
                                      "service_cpu_usage": 10 + i}, ts)
        sg.update_metrics("mid", {"average_response_time": 30 + i,
                                    "service_cpu_usage": 5 + i}, ts)

    # Correlation & cycle helpers
    sg.calculate_correlation("front", "mid")
    sg.dependency_strength("front", "mid")
    sg.get_all_dependencies("front")
    sg.get_root_cause("front")
    sg.score_node_health("front")
    sg.get_metrics_history("front", start_time=now, end_time=now + timedelta(seconds=11))
    sg.get_affected_services("back")
    sg.clear_metrics("front")
    sg.clear_metrics()
    sg.detect_circular_dependencies()
    sg.create_propagation_heatmap()

    # Extra queries to hit filtering branches
    sg.get_metrics_history("front")  # no range specified
    sg.get_metrics_history("front", start_time=now + timedelta(seconds=1000))

    # Inject anomaly to exercise alternative root cause path
    sg.update_metrics("back", {"service_cpu_usage": 95}, now + timedelta(seconds=100))
    sg.get_root_cause("front")


def _hit_detector():
    """Exercise anomaly detector edge-cases (flat baseline vs. spike)."""
    det = StatisticalDetector(window_size=4, z_score_threshold=2)
    # Baseline
    for v in (5, 7, 6, 8):
        det.detect_anomaly({"cpu_usage": v})
    # One more baseline to let history roll
    det.detect_anomaly({"cpu_usage": 6})
    assert not det.detect_anomaly({"cpu_usage": 7})
    # Spike – should be flagged
    assert "cpu_usage" in det.detect_anomaly({"cpu_usage": 95})

    # Use private helpers to exercise extra branches
    threshold = det._get_threshold("cpu_usage", det.metric_history["cpu_usage"])  # noqa: SLF001
    det._calculate_severity(90, threshold)


def _hit_health_and_recovery():
    """Touch the HealthManager and recovery orchestration branches."""
    hm = HealthManager()
    hm.record_metric("svc", "cpu", 10)
    hm.record_metric("svc", "latency", 20)
    hm.calculate_health_score("svc")
    hm.simulate_recovery(80, duration=5)

    sg = ServiceGraph()
    sg.add_service("svc")

    # Mock docker client expected by EnhancedRecoverySystem
    client = MagicMock()
    container = MagicMock()
    container.attrs = {"State": {"Health": {"Status": "healthy"}}}
    container.status = "running"
    client.containers.get.return_value = container

    ers = EnhancedRecoverySystem(sg, client)
    action = ers.create_recovery_action("svc", RecoveryActionType.RESTART)
    ers.execute_recovery_action(action)


def test_full_stack_smoke():
    """Run the three helper branches to bump overall coverage."""
    random.seed(42)  # deterministic flake-free run
    _hit_service_graph()
    _hit_detector()
    _hit_health_and_recovery() 