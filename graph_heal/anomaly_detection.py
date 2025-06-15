from __future__ import annotations

"""Minimal anomaly‐detection helpers used by the legacy test-suite.

These classes wrap the real :class:`graph_heal.improved_statistical_detector.StatisticalDetector`
so that we do not duplicate detection logic while keeping the public API that
older notebooks / tests expect.
"""

from datetime import datetime
from typing import Dict, List, Any

from graph_heal.improved_statistical_detector import StatisticalDetector as _CoreDetector

__all__ = [
    "StatisticalAnomalyDetector",
    "GraphAnomalyDetector",
]

# Backward-compat alias so code can still do `from graph_heal.anomaly_detection import StatisticalDetector`.
StatisticalDetector = _CoreDetector  # type: ignore  # noqa: N816


class StatisticalAnomalyDetector:
    """Service-centric wrapper around the core StatisticalDetector.

    The original interface consumed a *service_statuses* mapping that looks like

    ```python
    {
        "service_a": {"metrics": {"cpu": 12.3, "mem": 42}},
        "service_b": {"metrics": {…}},
    }
    ```

    The wrapper feeds each metric individually to the underlying detector and
    aggregates anomaly reports into a flat list.
    """

    def __init__(self, window_size: int = 5, z_score_threshold: float = 3.0):
        # The legacy detector defaulted to a very small history window so that
        # unit-test fixtures with <10 samples still trigger anomalies. To keep
        # behaviour consistent, we lower the default window from 30 ➜ 5 while
        # still honouring any explicit *window_size* argument.
        self._det = _CoreDetector(window_size=window_size, z_score_threshold=z_score_threshold)

        # Collect every anomaly ever reported so older callers can inspect the
        # timeline via ``get_all_anomalies``.
        self._all_anomalies: List[Dict[str, Any]] = []

    # ------------------------------------------------------------------
    # Compatibility layer ------------------------------------------------
    # ------------------------------------------------------------------
    def detect_anomalies(self, service_statuses: Dict[str, Dict[str, Any]]):
        anomalies: List[Dict[str, Any]] = []
        for svc, info in service_statuses.items():
            metrics = info.get("metrics", {})
            # Core detector expects {metric_name: value}
            detected = self._det.detect_anomaly(metrics)
            if detected:
                for m_name, meta in detected.items():
                    meta = dict(meta)  # copy to avoid mutating core output
                    meta.update({"service": svc})
                    anomalies.append(meta)

        # Persist for ``get_all_anomalies``.
        if anomalies:
            self._all_anomalies.extend(anomalies)
        return anomalies

    # ------------------------------------------------------------------
    # Legacy helpers ----------------------------------------------------
    # ------------------------------------------------------------------
    def get_all_anomalies(self):  # noqa: D401
        """Return a list with **all** anomalies detected so far.

        Older notebooks relied on this convenience accessor instead of
        maintaining their own history. We simply expose the collected list.
        """
        return list(self._all_anomalies)


class GraphAnomalyDetector:  # pragma: no cover – placeholder for legacy code
    """Placeholder – original implementation relied on GNN models.

    For unit tests we only need successful construction, so this minimal stub
    captures the signature and offers a no-op `detect_anomalies`.
    """

    def __init__(self, *_, **__):
        self._stat = StatisticalAnomalyDetector()

    def detect_anomalies(self, service_statuses: Dict[str, Dict[str, Any]]):
        # Simply delegate to statistical detector for stub behaviour
        return self._stat.detect_anomalies(service_statuses) 