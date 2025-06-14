import unittest
from graph_heal.anomaly_detection import StatisticalAnomalyDetector, GraphAnomalyDetector

class TestAnomalyDetection(unittest.TestCase):
    def test_statistical_detector_no_anomaly(self):
        detector = StatisticalAnomalyDetector(z_score_threshold=2.5)
        service_statuses = {
            "svc": {"metrics": {"cpu": 1}},
        }
        # Feed normal values
        for v in [1, 2, 3, 4, 5]:
            service_statuses["svc"]["metrics"]["cpu"] = v
            detector.detect_anomalies(service_statuses)
        # No anomaly expected
        self.assertEqual(len(detector.detect_anomalies(service_statuses)), 0)

    def test_statistical_detector_with_anomaly(self):
        detector = StatisticalAnomalyDetector(z_score_threshold=2.0)
        service_statuses = {
            "svc": {"metrics": {"cpu": 1}},
        }
        for v in [1, 2, 3, 4, 5]:
            service_statuses["svc"]["metrics"]["cpu"] = v
            detector.detect_anomalies(service_statuses)
        # Now inject an anomaly
        service_statuses["svc"]["metrics"]["cpu"] = 100
        anomalies = detector.detect_anomalies(service_statuses)
        self.assertGreaterEqual(len(anomalies), 1)

    def test_graph_detector_initialization(self):
        detector = GraphAnomalyDetector()
        self.assertIsNotNone(detector)

if __name__ == '__main__':
    unittest.main() 