import math
from graph_heal.improved_statistical_detector import StatisticalDetector


def _feed(det, vals):
    for v in vals:
        det.detect_anomaly({"cpu_usage": v})


def test_all_paths():
    det = StatisticalDetector(window_size=3, z_score_threshold=2)

    # empty / NaN
    assert det.detect_anomaly({}) == {}
    assert det.detect_anomaly({"cpu_usage": math.nan}) == {}

    # gradual ramp baseline
    _feed(det, [10, 12, 14, 16])
    assert "cpu_usage" in det.detect_anomaly({"cpu_usage": 18})

    # one more baseline value to fill window
    det.detect_anomaly({"cpu_usage": 20})

    # spike should now trigger
    high = det.detect_anomaly({"cpu_usage": 70})
    assert "cpu_usage" in high 