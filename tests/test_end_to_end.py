import json
import os
import tempfile
import unittest
from datetime import datetime

# Load the evaluator dynamically from its script path to avoid packaging
# issues in test environments where `graph-heal/scripts` is not a Python
# package.

import importlib.util
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve().parent.parent / "graph-heal" / "scripts" / "evaluate_advanced_metrics.py"
spec = importlib.util.spec_from_file_location("evaluate_advanced_metrics", SCRIPT_PATH)
module = importlib.util.module_from_spec(spec)  # type: ignore
spec.loader.exec_module(module)  # type: ignore

AdvancedMetricsEvaluator = module.AdvancedMetricsEvaluator


class TestEndToEndEvaluator(unittest.TestCase):
    """Minimal integration‐like sanity test.

    Ensures that the evaluator can load a *real* scenario file in the
    "services-wrapper" format without throwing and that at least one metric is
    non-zero. Serves as a CI guard against path resolution and None-comparison
    regressions.
    """

    def _make_dummy_capture(self) -> str:
        """Return path to a transient JSON capture following schema v1."""
        snapshots = []
        t0 = int(datetime.now().timestamp())
        phases = [("baseline", 5), ("fault", 5), ("recovery", 5)]

        for phase, count in phases:
            for i in range(count):
                snapshots.append({
                    "version": 1,
                    "timestamp": t0 + len(snapshots),
                    "services": {
                        "service_a": {
                            "phase": phase,
                            "health": 1.0 if phase == "baseline" else 0.4,
                            "availability": 100 if phase == "baseline" else 60
                        },
                        "service_b": {
                            "phase": phase,
                            "health": 1.0,
                            "availability": 100
                        }
                    }
                })

        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
        with open(tmp.name, "w") as fh:
            json.dump(snapshots, fh)
        return tmp.name

    def test_evaluator_produces_non_zero_metrics(self):
        path = self._make_dummy_capture()
        evaluator = AdvancedMetricsEvaluator(path)

        # Choose some arbitrary timestamps to satisfy API (not used heavily)
        fault_ts = [datetime.now()]
        results = evaluator.run_evaluation("service_a", "cpu", fault_ts)

        numeric_vals = [v for v in results.values() if isinstance(v, (int, float))]
        self.assertTrue(any(v != 0 for v in numeric_vals), "All metrics are zero – evaluator failed to read capture")

        # Clean up
        os.remove(path)


if __name__ == "__main__":
    unittest.main() 