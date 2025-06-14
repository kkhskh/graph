import importlib, math
from unittest.mock import MagicMock

ServiceGraph = importlib.import_module("graph_heal.service_graph").ServiceGraph  # type: ignore[attr-defined]
EnhancedRecoverySystem = importlib.import_module("graph_heal.recovery_system").EnhancedRecoverySystem  # type: ignore[attr-defined]
RecoveryActionType = importlib.import_module("graph_heal.recovery_system").RecoveryActionType  # type: ignore[attr-defined]

anomaly_mod = importlib.import_module("graph_heal.anomaly_detection")
StatisticalAnomalyDetector = anomaly_mod.StatisticalAnomalyDetector if hasattr(anomaly_mod, "StatisticalAnomalyDetector") else anomaly_mod.StatisticalDetector  # type: ignore[attr-defined]
GraphAnomalyDetector = getattr(anomaly_mod, "GraphAnomalyDetector", None)
AnomalyManager = getattr(anomaly_mod, "AnomalyManager", None)


def test_cycle_and_heatmap():
    sg = ServiceGraph()
    for n in ("a", "b", "c"):
        sg.add_service(n)
    sg.add_dependency("a", "b")
    sg.add_dependency("b", "c")
    sg.add_dependency("c", "a")

    assert sg.get_dependencies("a")

    # inject metrics
    sg.update_metrics("a", {"average_response_time": 1})
    sg.update_metrics("b", {"average_response_time": 2})
    sg.update_metrics("c", {"average_response_time": 3})

    heat = sg.create_propagation_heatmap("a")
    assert heat.shape[0] > 0


def test_recovery_success():
    sg = ServiceGraph()
    sg.add_service("svc")
    ers = EnhancedRecoverySystem(sg, MagicMock())
    action = ers.create_recovery_action("svc", RecoveryActionType.RESTART)

    # monkeypatch execute action to succeed immediately
    ers._execute_action = lambda a: True  # type: ignore
    assert ers.execute_recovery_action(action)


def test_bayesian_localizer():
    if GraphAnomalyDetector is None or AnomalyManager is None:
        return  # skip if legacy detector missing
    det = StatisticalAnomalyDetector(window_size=2, z_score_threshold=1)
    gdet = GraphAnomalyDetector()
    mgr = AnomalyManager([det, gdet])
    state = {"service_statuses": {"x": {"metrics": {"cpu": 1}}}}
    mgr.detect_anomalies(state)
    assert mgr.get_all_anomalies() is not None 