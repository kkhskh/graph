#!/usr/bin/env python3
"""Baseline-vs-GraphHeal anomaly-detection comparison helper.

Usage (stand-alone):
    python -m graph_heal.scripts.baseline_vs_graphheal \
        --capture data/captures/sample.json --out plots/

The script expects *capture* JSON files with a flat list of records.  Each
record **must** expose two keys:

* ``value`` – numeric metric sample (float/int)
* ``is_anomaly`` – boolean ground-truth label

If those keys differ in your dataset use ``--value-key`` / ``--label-key`` to
override.

Outputs
-------
1. Bar plot ``precision_recall_bar.png`` comparing baseline z-score vs. the
   real :class:`graph_heal.improved_statistical_detector.StatisticalDetector`.
2. Line plot ``f1_zscore_sweep.png`` with F1 versus *z*-threshold for the
   baseline detector.
3. Prints the metrics table to stdout and exits 0 regardless (analysis only).
"""
from __future__ import annotations

import argparse
import json
import logging
import math
import pathlib
import sys
from typing import List, Tuple

import matplotlib.pyplot as plt
import numpy as np

# ---------------------------------------------------------------------------
# Ensure project root is on sys.path BEFORE importing local packages
# ---------------------------------------------------------------------------
_ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from graph_heal.improved_statistical_detector import StatisticalDetector

logger = logging.getLogger("baseline_vs_graphheal")

# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------

def _precision_recall_f1(tp: int, fp: int, fn: int) -> Tuple[float, float, float]:
    if tp + fp == 0:
        precision = 0.0
    else:
        precision = tp / (tp + fp)
    if tp + fn == 0:
        recall = 0.0
    else:
        recall = tp / (tp + fn)
    if precision + recall == 0:
        f1 = 0.0
    else:
        f1 = 2 * precision * recall / (precision + recall)
    return precision, recall, f1


def baseline_zscore(values: List[float], window: int, z_thresh: float) -> List[bool]:
    """Simple rolling z-score detector: mark *values[i]* as anomaly if the
    absolute difference to the rolling mean of the *window* preceding samples
    exceeds *z_thresh*·std.
    The first *window* samples cannot be evaluated and are marked *False*.
    """
    out: List[bool] = [False] * len(values)
    if window < 2:
        return out
    for i in range(window, len(values)):
        win = values[i - window : i]
        mu = float(np.mean(win))
        sigma = float(np.std(win))
        if sigma == 0:
            continue
        if abs(values[i] - mu) >= z_thresh * sigma:
            out[i] = True
    return out


# ---------------------------------------------------------------------------
# Main routine
# ---------------------------------------------------------------------------

def main(argv: List[str] | None = None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--capture", default="data/captures/sample.json", help="Path to capture JSON file")
    p.add_argument("--out", "--outdir", default="plots", help="Directory to dump PNG plots")
    p.add_argument("--window", type=int, default=30, help="Rolling window size for baseline detector")
    p.add_argument("--z", type=float, default=3.0, help="z-score threshold for baseline detector")
    p.add_argument("--value-key", default="value", help="Key that holds the numeric metric value (flat captures)")
    p.add_argument("--label-key", default="is_anomaly", help="Key for ground truth boolean label (flat captures)")

    # Nested multi-service capture helpers ---------------------------------
    p.add_argument("--service", help="Service name inside nested 'services' captures (e.g. service_a)")
    p.add_argument("--metric", help="Metric field inside the chosen service (e.g. host_cpu)")
    p.add_argument("--label-from-phase", action="store_true", dest="lbl_phase", help="Derive boolean labels from service phase != baseline")

    args = p.parse_args(argv)

    capture_path = pathlib.Path(args.capture)
    if not capture_path.exists():
        logger.error("Capture %s not found – aborting", capture_path)
        return 0

    with capture_path.open("r", encoding="utf-8") as fh:
        records = json.load(fh)

    # ------------------------------------------------------------------
    # Flatten capture ---------------------------------------------------
    # ------------------------------------------------------------------
    if args.service and args.metric:
        values = []
        labels = []
        for rec in records:
            if "services" in rec:
                svc = rec["services"].get(args.service)
            else:
                svc = rec.get(args.service)
            if svc is None:
                # skip missing service entry
                continue
            v_raw = svc.get(args.metric)
            # Only accept numeric samples
            if v_raw is None:
                continue
            try:
                values.append(float(v_raw))
            except (TypeError, ValueError):
                # non-numeric -> skip record
                continue

            if args.lbl_phase:
                labels.append(svc.get("phase", "baseline") != "baseline")
            else:
                labels.append(bool(svc.get(args.label_key, False)))

        if not values:
            logger.error("No usable samples extracted for service %s metric %s", args.service, args.metric)
            return 0
        logger.info("Extracted %d samples for %s/%s", len(values), args.service, args.metric)

    else:
        # Flat record schema (value/is_anomaly at top level)
        values = [float(rec[args.value_key]) for rec in records]
        labels = [bool(rec[args.label_key]) for rec in records]

    # Baseline detection ----------------------------------------------------
    base_pred = baseline_zscore(values, window=args.window, z_thresh=args.z)

    # GraphHeal detector ----------------------------------------------------
    det = StatisticalDetector(window_size=args.window, z_score_threshold=args.z)
    gh_pred: List[bool] = []
    for v in values:
        res = det.detect_anomaly({"cpu_usage": v})  # metric name arbitrary
        gh_pred.append(bool(res))

    # Evaluate --------------------------------------------------------------
    def _score(pred: List[bool]):
        tp = sum(p and t for p, t in zip(pred, labels))
        fp = sum(p and not t for p, t in zip(pred, labels))
        fn = sum((not p) and t for p, t in zip(pred, labels))
        return _precision_recall_f1(tp, fp, fn)

    p_b, r_b, f1_b = _score(base_pred)
    p_gh, r_gh, f1_gh = _score(gh_pred)

    print("\n=== Detection metrics ===")
    print(f"Baseline  – precision {p_b:.3f} recall {r_b:.3f} F1 {f1_b:.3f}")
    print(f"GraphHeal – precision {p_gh:.3f} recall {r_gh:.3f} F1 {f1_gh:.3f}\n")

    out_dir = pathlib.Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Plot 1: bar precision/recall -----------------------------------------
    fig, ax = plt.subplots(figsize=(4, 3))
    x = np.arange(2)
    width = 0.35
    bars1 = ax.bar(x - width / 2, [p_b, r_b], width, label="Baseline")
    bars2 = ax.bar(x + width / 2, [p_gh, r_gh], width, label="GraphHeal")
    ax.set_xticks(x)
    ax.set_xticklabels(["Precision", "Recall"])
    ax.set_ylim(0, 1)
    ax.legend(loc="lower right")
    ax.set_title("Detection quality")
    fig.tight_layout()
    fig.savefig(out_dir / "precision_recall_bar.png", dpi=150)
    plt.close(fig)

    # Plot 2: F1 vs z-threshold sweep for baseline -------------------------
    zs = np.linspace(0.5, 6.0, 24)
    f1s = []
    for z_val in zs:
        preds = baseline_zscore(values, window=args.window, z_thresh=z_val)
        _, _, f1 = _score(preds)
        f1s.append(f1)
    fig2, ax2 = plt.subplots(figsize=(4, 3))
    ax2.plot(zs, f1s, marker="o", label="Baseline z-score")
    ax2.axhline(f1_gh, color="tab:orange", linestyle="--", label="GraphHeal static")
    ax2.set_xlabel("z-score threshold")
    ax2.set_ylabel("F1-score")
    ax2.set_title("F1 vs. z-threshold (baseline)")
    ax2.legend(loc="lower right")
    fig2.tight_layout()
    fig2.savefig(out_dir / "f1_zscore_sweep.png", dpi=150)
    plt.close(fig2)

    print(f"Plots written to {out_dir.resolve()}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main()) 