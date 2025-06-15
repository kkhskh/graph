#!/usr/bin/env bash
# One-click capture + evaluation for GRAPH-HEAL experiments.
#
# Usage:
#   ./run_capture_and_eval.sh                   # normal 60-300-60
#   ./run_capture_and_eval.sh --mode quick      # 10-20-10 fast loop
#   ./run_capture_and_eval.sh --mode stress     # 120-600-120 heavy load
#   ./run_capture_and_eval.sh --augment         # enrich host metrics
#
# The script writes the capture to ./experiments and feeds the absolute path
# straight into the evaluator so no brittle path juggling is required.

set -euo pipefail

# Ensure repo root is on PYTHONPATH so helper modules resolve when the script
# is invoked from arbitrary working directories.
export PYTHONPATH="${PYTHONPATH:-$(pwd)}"

# ---------------------------------------------------------------------------
# Configurable knobs (override with environment variables or flags)
# ---------------------------------------------------------------------------
BASE=${BASE:-60}        # seconds of healthy baseline traffic
FAULT=${FAULT:-300}     # seconds under injected CPU stress
REC=${REC:-60}          # seconds of recovery traffic
RUN="cpu_fault_$(date +%s).json"
CAP="$PWD/experiments/$RUN"

# default mode
MODE="normal"

# Optional plot flag
PLOT=false

# Honour optional --augment flag
AUGMENT=false
for arg in "$@"; do
  if [[ "$arg" == "--augment" ]]; then
    AUGMENT=true
  elif [[ "$arg" == "--mode"* ]]; then
    MODE="${arg#--mode }"
  elif [[ "$arg" == "--plot" ]]; then
    PLOT=true
  fi
done

case "$MODE" in
  quick)
    BASE=10
    FAULT=20
    REC=10
    SLEEP_ARG="--sleep 0.2"
    ;;
  stress)
    BASE=120
    FAULT=600
    REC=120
    SLEEP_ARG="--sleep 1"
    ;;
  *) # normal
    SLEEP_ARG="--sleep 1"
    ;;
esac

mkdir -p "$(dirname "$CAP")"

echo "[GRAPH-HEAL] Collecting scenario -> $CAP"
python3 graph-heal/tools/capture_multiservice.py \
        --baseline "$BASE" \
        --fault "$FAULT" \
        --recovery "$REC" \
        $SLEEP_ARG \
        --out "$CAP"

if $AUGMENT; then
  echo "[GRAPH-HEAL] Enriching capture with host metrics"
  python3 graph-heal/tools/augment_json.py "$CAP"
fi

echo "[GRAPH-HEAL] Evaluating scenario"
python3 graph-heal/scripts/evaluate_advanced_metrics.py --scenario "$CAP"

if $PLOT; then
  echo "[GRAPH-HEAL] Generating comparison plots"
  python3 graph-heal/scripts/baseline_vs_graphheal.py --capture "$CAP" --out plots
fi 