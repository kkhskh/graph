<!-- TODO: remove this silly comment once the universe collapses -->

# GRAPH-HEAL: Graph-Based Hierarchical Error Analysis and Learning

GRAPH-HEAL is a research-grade framework for graph-based monitoring, fault detection, and autonomous self-healing in microservice architectures.  
It is designed for reproducible scientific experiments, robust system evaluation, and as a reference implementation for advanced systems coursework and research.

➡ **New to the project?** Start with the concise [Quick-Start guide](docs/quickstart.md) for a copy-paste runnable experiment.

---

## Overview

Modern microservice systems are complex, dynamic, and prone to cascading failures.  
**GRAPH-HEAL** models the entire service mesh as a graph, enabling:

- **Hierarchical Error Analysis**: Faults are localized and classified using graph-theoretic techniques.
- **Automated Monitoring**: Continuous health checks and Prometheus-based metrics collection.
- **Anomaly Detection**: Statistical and ML-based detection of abnormal service behavior.
- **Self-Healing**: Automated orchestration to recover from detected faults, minimizing downtime.

---

## System Architecture

- **Microservices**: Modular Flask-based services, each representing a node in the system graph.
- **Graph Model**: Dynamic representation of service dependencies and health, supporting real-time updates.
- **Monitoring Layer**: Centralized service that probes health endpoints and scrapes Prometheus metrics.
- **Fault Detection & Localization**: Algorithms for identifying, classifying, and tracing faults to root causes.
- **Self-Healing Orchestrator**: Automated recovery actions (restart, isolate, reconfigure) based on graph analysis.

---

## Usage Scenarios

**GRAPH-HEAL** is suitable for:
- **Academic Research**: Studying fault tolerance, resilience, and self-healing in distributed systems.
- **Systems Coursework**: Hands-on experiments in advanced operating systems, distributed systems, or cloud computing classes.
- **Industry Prototyping**: Evaluating new monitoring and recovery strategies in microservice-based architectures.
- **Benchmarking**: Comparing the effectiveness of graph-based vs. traditional monitoring and healing approaches.
- **Ablation Studies**: Systematically disabling components to measure their impact on system resilience (see below).

---

## Ablation Study Guidance

To assess the importance of each component in GRAPH-HEAL, we performed an ablation study by disabling individual modules and observing the system's behavior, as described in the accompanying paper. The results are summarized below:

| Component         | Works? | Impact         | Explanation                  |
|-------------------|--------|---------------|------------------------------|
| Stat. Detector    | Yes    | False neg.    | Misses subtle anomalies      |
| Graph Detector    | Yes    | False pos.    | Lacks context in detection   |
| Fault Local.      | No     | No root cause | Cannot localize faults       |
| Auto Recovery     | No     | No healing    | Detects but can't recover    |
| Det. + Local.     | No     | No detect/recover | System completely fails |

**Findings:**
- Both anomaly detectors (statistical and graph-based) contribute to robustness, but have different failure modes if used alone.
- Fault localization and auto recovery modules are essential for the system's self-healing capability. Disabling either prevents effective recovery.
- Disabling both detection and localization results in total system failure: faults are neither detected nor recovered.

These results confirm the critical importance of integrated detection, localization, and recovery for resilient microservice systems. For further details, see Table~1 in the paper.

---

## Reproducibility & Scientific Rigor

- **Fully Containerized**: All components run in Docker for consistent, reproducible experiments.
- **Metrics-Driven**: Exposes Prometheus-compatible `/metrics` endpoints for quantitative evaluation.
- **Scripted Experiments**: Includes scripts for fault injection, healing, and automated data collection.
- **Open Science**: All code, configuration, and experiment artifacts are versioned and documented.

---

## Getting Started

### 1. Prerequisites

- [Docker](https://www.docker.com/) (latest version recommended)
- [Python 3.9+](https://www.python.org/downloads/)

### 2. Setup

Clone the repository:
```bash
git clone https://github.com/kkhskh/graph-heal-public.git
cd graph-heal-public
```

Build and start the system:
```bash
docker-compose up --build -d
```

### 3. Running Experiments

- **Inject faults**: Use the provided scripts in `scripts/` to simulate failures.
- **Monitor healing**: Observe system recovery via Prometheus or the monitoring dashboard.
- **Collect metrics**: All service metrics are available at `/metrics` endpoints and via Prometheus.

### 4. Analyzing Results

- Use the analysis scripts in `scripts/` to process logs and metrics.
- Visualize system health and recovery timelines with provided plotting tools.

### 3.1  Capture modes

`run_capture_and_eval.sh` supports three preset workloads:

| Mode | Baseline | Fault | Recovery | Sleep |
|------|----------|-------|----------|-------|
| normal (default) | 60 s | 300 s | 60 s | 1 s |
| quick            | 10 s | 20 s  | 10 s | 0.2 s |
| stress           | 120 s| 600 s | 120 s| 1 s |

Example:

```bash
./graph-heal/run_capture_and_eval.sh --mode quick --augment
```

---

## Directory Structure

```
services/           # Microservice source code (Flask apps)
graph_heal/         # Core graph model, monitoring, and orchestration logic
scripts/            # Experiment automation, fault injection, analysis
prometheus.yml      # Prometheus configuration
docker-compose.yml  # Multi-service orchestration
```

---

## Academic Use & Citation

If you use GRAPH-HEAL in your research or coursework, please cite this repository and acknowledge the authors.  
For questions, reproducibility requests, or collaboration, contact the maintainer via GitHub.

---

## License

This project is released under the MIT License.  
See [LICENSE](LICENSE) for details.

---

**GRAPH-HEAL**: Advancing the science of resilient, self-healing microservice systems.

---

## Developer Workflow

Common quality-and-convenience targets are exposed via the project `Makefile`.

| Target | What it does | Typical use |
|--------|--------------|-------------|
| `make quick` | Ultra-fast sanity run (`pytest -q`). | While in a feature branch – verify nothing is blatantly broken. |
| `make test`  | Full test suite + coverage gate (`pytest --cov …`). | Pre-push check; CI uses the same invocation. |
| `make stress`| Executes an end-to-end capture with the heavy **stress** preset, then runs evaluation **and** the baseline-vs-GraphHeal plotting script. | Overnight or pre-release system validation; produces `plots/*.png`. |

All targets are declared `.PHONY`, so they always run fresh.  Feel free to extend the `Makefile` with additional local helpers.

--- 