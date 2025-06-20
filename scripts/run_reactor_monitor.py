#!/usr/bin/env python3
"""Run Graph-Heal against live Prometheus + (optionally) real OPC-UA adapter.

Example
-------
    python scripts/run_reactor_monitor.py \
        --prom-url http://localhost:9090 \
        --adapter-endpoint opc.tcp://plc.example.com:4840 \
        --thresholds config/anomaly_thresholds.yaml \
        --recovery   config/recovery_strategies.yaml

The script:
1. Builds the reactor service graph (re-using build_reactor_graph() helper).
2. Loads anomaly thresholds & recovery strategies from YAML (if present).
3. Creates the ReactorRecoveryAdapter (dry-run if python-opcua missing).
4. Starts PrometheusServiceMonitor with the metric map defined in
   ``metric_map.yaml`` (see below).
5. Runs indefinitely, printing a concise anomaly summary every N seconds.

Metric-map configuration
------------------------
Create ``config/metric_map.yaml`` of the form::

    TempSensorAggregator:
      temperature: 'reactor_temp_celsius'
    PressureSensorAggregator:
      pressure: 'reactor_pressure_bar'
    ReactorControl:
      control_loop_latency: 'control_loop_latency_ms'

Keys are service IDs, values are PromQL expressions.

If no YAML is given the script falls back to the scalar demo map used in
prom_demo.py so you can run it on a laptop without Prometheus.
"""
from __future__ import annotations

import argparse
import logging
import pathlib
import time
import yaml
import re
from typing import Optional

# ---------------------------------------------------------------------------
# Import *full* GraphHeal implementation – fall back to explicit file load if a
# minimalist stub shadows the in-tree version on sys.path.  This mirrors the
# defensive logic used in `reactor_simulation.py` so that anomaly detection,
# propagation, and recovery are available even when an old wheel is installed.
# ---------------------------------------------------------------------------

try:
    from graph_heal.graph_heal import GraphHeal  # type: ignore

    # If we accidentally grabbed the stub, it won't have `anomaly_thresholds`.
    if not hasattr(GraphHeal, "anomaly_thresholds"):
        raise AttributeError  # trigger fallback loader

except (ImportError, AttributeError):
    import importlib.util
    import pathlib
    import sys

    _full_path = pathlib.Path(__file__).resolve().parents[1] / "graph_heal" / "graph_heal.py"
    spec = importlib.util.spec_from_file_location("graph_heal.graph_heal_full", _full_path)
    if spec and spec.loader:
        _mod = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = _mod  # make repeat imports pick it up
        spec.loader.exec_module(_mod)  # type: ignore[arg-type]
        GraphHeal = _mod.GraphHeal  # type: ignore[attr-defined]

# ---------------------------------------------------------------------------
# Import helper modules and ensure we have the *full* PrometheusServiceMonitor
# implementation.  This block was accidentally removed in the previous edit.
# ---------------------------------------------------------------------------

from scripts.reactor_simulation import build_reactor_graph  # topology helper
from scripts.reactor_recovery import ReactorRecoveryAdapter

# Ensure we grab the *full* monitoring module instead of any stub that could be
# installed elsewhere on sys.path.
try:
    from graph_heal.monitoring import PrometheusServiceMonitor  # type: ignore
except ImportError:
    import importlib.util as _imp_util
    import sys as _sys

    _mon_path = pathlib.Path(__file__).resolve().parents[1] / "graph_heal" / "monitoring.py"
    _mon_spec = _imp_util.spec_from_file_location("graph_heal.monitoring_full", _mon_path)
    if _mon_spec and _mon_spec.loader:
        _mon_mod = _imp_util.module_from_spec(_mon_spec)
        _sys.modules[_mon_spec.name] = _mon_mod
        _mon_spec.loader.exec_module(_mon_mod)  # type: ignore[arg-type]
        PrometheusServiceMonitor = _mon_mod.PrometheusServiceMonitor  # type: ignore[attr-defined]

# ---------------------------------------------------------------------------
# Hot-patch – interpret *scalar(NUMBER)* expressions regardless of the concrete
# PrometheusServiceMonitor implementation that was eventually imported. Some
# users may have an old graph-heal package installed in their site-packages
# directory which shadows the in-tree implementation. That older version lacks
# the built-in scalar() shortcut.  The snippet below wraps/overrides the
# ``_query`` method so the demo spike works even with the shadowed module.
# ---------------------------------------------------------------------------

if not getattr(PrometheusServiceMonitor, "__SCALAR_PATCHED__", False):
    _orig_query = PrometheusServiceMonitor._query  # type: ignore[attr-defined]

    def _query_with_scalar(self, prom_query: str) -> Optional[float]:  # type: ignore[override]
        match = re.fullmatch(r"scalar\(\s*([\d.]+)\s*\)", prom_query)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                return None
        # Fallback to original implementation (HTTP request etc.)
        return _orig_query(self, prom_query)

    PrometheusServiceMonitor._query = _query_with_scalar  # type: ignore[assignment]
    PrometheusServiceMonitor.__SCALAR_PATCHED__ = True

# ---------------------------------------------------------------------------
# Dependency-free demo mode – if `requests` is missing but every PromQL string
# is a simple *scalar(NUMBER)* expression we still want the polling thread to
# run.  Replace the guard in the monitoring module so `start()` doesn't abort.
# ---------------------------------------------------------------------------

import graph_heal.monitoring as _gh_mon

if getattr(_gh_mon, "requests", None) is None:
    _gh_mon.requests = object()  # type: ignore[attr-defined]

_LOG = logging.getLogger("run-monitor")

DEFAULT_METRIC_MAP = {
    "TempSensorAggregator":   {"temperature": "scalar(95)"},
    "PressureSensorAggregator": {"pressure": "scalar(180)"},
    "ReactorControl":        {"control_loop_latency": "scalar(300)"},
}

# Synthetic spike for immediate demo ------------------------------------------
DEFAULT_METRIC_MAP["TempSensorAggregator"]["temperature"] = "scalar(120)"


def parse_args():
    ap = argparse.ArgumentParser(description="Run Graph-Heal with live Prometheus ingestion")
    ap.add_argument("--prom-url", default="http://localhost:9090", help="Prometheus base URL")
    ap.add_argument("--metric-map", default="config/metric_map.yaml", help="YAML mapping service→PromQL")
    ap.add_argument("--thresholds", default="config/anomaly_thresholds.yaml", help="YAML anomaly thresholds")
    ap.add_argument("--recovery", default="config/recovery_strategies.yaml", help="YAML recovery strategies")
    ap.add_argument("--adapter-endpoint", default="", help="OPC-UA endpoint, empty = dry-run")
    ap.add_argument("--summary-interval", type=int, default=30, help="Seconds between health summaries")
    return ap.parse_args()


def load_yaml(path: str | pathlib.Path) -> dict:
    if not path:
        return {}
    p = pathlib.Path(path)
    if p.is_dir():
        return {}
    if p.exists():
        return yaml.safe_load(p.read_text()) or {}
    _LOG.warning("YAML file %s not found; using empty defaults", p)
    return {}


def main():
    args = parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s:%(name)s:%(message)s")

    # ------------------------------------------------- build graph
    gh: GraphHeal = build_reactor_graph()

    # ------------------------------------------------- load configs
    gh.anomaly_thresholds.update(load_yaml(args.thresholds))
    gh.recovery_strategies.update(load_yaml(args.recovery))

    # ------------------------------------------------- metric map
    metric_map = load_yaml(args.metric_map) or DEFAULT_METRIC_MAP
    if metric_map is DEFAULT_METRIC_MAP:
        _LOG.warning("Using DEFAULT_METRIC_MAP – install Prometheus or provide metric_map.yaml for real data")

    # ------------------------------------------------- recovery adapter + monitor
    gh.recovery_adapter = ReactorRecoveryAdapter(args.adapter_endpoint or None)
    monitor = PrometheusServiceMonitor(gh, prom_url=args.prom_url, metric_map=metric_map, poll_interval=1)
    monitor.start()
    _LOG.info("Prometheus monitor started against %s", args.prom_url)

    try:
        last_report = time.time()
        while True:
            if time.time() - last_report >= args.summary_interval:
                _LOG.info("Health summary: %s", gh.get_health_summary())
                last_report = time.time()
            time.sleep(1)
    except KeyboardInterrupt:
        _LOG.info("Interrupted by user – shutting down…")
    finally:
        monitor.stop()
        if hasattr(gh, "recovery_adapter"):
            gh.recovery_adapter.close()  # type: ignore[attr-defined]


if __name__ == "__main__":
    main() 