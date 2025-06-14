import math
from graph_heal.anomaly_detection import StatisticalAnomalyDetector


def test_empty_series_returns_no_anomaly():
    det = StatisticalAnomalyDetector(window_size=5)
    anomalies = det.detect_anomalies({})
    assert anomalies == []


def test_all_nan_series_returns_no_anomaly():
    det = StatisticalAnomalyDetector(window_size=5)
    statuses = {
        "svc": {"metrics": {"cpu": math.nan, "mem": math.nan}}
    }
    anomalies = det.detect_anomalies(statuses)
    assert anomalies == []


def test_huge_spike_detected():
    det = StatisticalAnomalyDetector(window_size=5, z_score_threshold=2.0)
    statuses = {"svc": {"metrics": {"cpu": 1}}}
    # feed normal values
    for v in [1, 2, 1, 2, 1]:
        statuses["svc"]["metrics"]["cpu"] = v
        det.detect_anomalies(statuses)
    # now spike
    statuses["svc"]["metrics"]["cpu"] = 10000
    anomalies = det.detect_anomalies(statuses)
    assert any(a["metric_name"] == "cpu" for a in anomalies) 