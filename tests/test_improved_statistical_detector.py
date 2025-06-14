import math
import importlib

StatisticalDetector = importlib.import_module("graph_heal.improved_statistical_detector").StatisticalDetector  # type: ignore[attr-defined]


def test_improved_detector_edge_cases():
    det = StatisticalDetector(window_size=4)

    # Empty input returns no anomalies
    assert det.detect_anomaly({}) == {}

    # NaN metrics should be ignored and produce no anomalies
    anomalies = det.detect_anomaly({"cpu_usage": math.nan})
    assert anomalies == {}

    # Gradual ramp stays under threshold
    for v in (10, 12, 14, 16):
        det.detect_anomaly({"cpu_usage": v})
    assert not det.detect_anomaly({"cpu_usage": 18})

    # Sudden spike triggers anomaly
    high = det.detect_anomaly({"cpu_usage": 95})
    assert "cpu_usage" in high