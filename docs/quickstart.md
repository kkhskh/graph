# GRAPH-HEAL Quick-Start 🚀

This page is the **minimum** you need to spin up the demo stack, inject a CPU
fault, collect metrics, and run the evaluator.

---

## 1. Prerequisites

```
Docker             # daemon must be running
Python ≥ 3.9       # any recent CPython is fine
```

The stack exposes:

* 5000-5004 – Flask services A-D `/metrics` + control endpoints
* 9090 – Prometheus UI / API

Make sure these ports are free on your host.

---

## 2. Boot the Stack

```bash
cd <repo-root>
docker compose up -d --build   # first time may take a minute
```

> **Tip**: If you modified service code inside the containers, do a full
> `docker compose down -v` before the `up -d --build` to avoid stale layers.

---

## 3. One-liner Experiment

From the repository root run:

```bash
./graph-heal/run_capture_and_eval.sh            # capture + evaluate
# OR add host-metric enrichment
./graph-heal/run_capture_and_eval.sh --augment
```

The helper script will:

1. Collect a 60-300-60 baseline/fault/recovery scenario into
   `./experiments/<timestamp>.json`.
2. (Optional) Enrich it with host CPU / memory / RTT metrics.
3. Feed the **absolute** capture path to the evaluator. No brittle copies or
   path juggling required.

At the end you'll get the key metrics directly on stdout **and** a
JSON dump under `results/advanced_metrics_evaluation.json`.

---

## 4. Custom Durations

Override the defaults via environment variables:

```bash
BASE=30 FAULT=120 REC=30 ./graph-heal/run_capture_and_eval.sh
```

---

## 5. Troubleshooting

* **Scenario file not found** – The evaluator now accepts absolute paths. Ensure
  you're passing the full path or use the helper script.
* **Prometheus connection refused** – Confirm the stack is running and port 9090
  isn't blocked by a firewall/VPN.
* **All metrics zero / NoneType errors** – Run `pytest -q` to execute the
  sanity test. If it fails, recent code changes likely broke the loader.

---

Happy experimenting! 🧪

---

## 6. Further Reading

* **Automated run helper** – `graph-heal/run_capture_and_eval.sh`
* **End-to-end sanity test** – `tests/test_end_to_end.py` (run with `pytest -q`) 