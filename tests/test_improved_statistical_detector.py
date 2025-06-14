import math
import importlib, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

StatisticalDetector = importlib.import_module("graph_heal.improved_statistical_detector").StatisticalDetector  # type: ignore[attr-defined]


def test_improved_detector_edge_cases():
    det = StatisticalDetector(window_size=4, z_score_threshold=3.0)

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
    assert high["cpu_usage"]["current"] == 95