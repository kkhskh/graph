.PHONY: quick test stress

# ---------------------------------------------------------------------------
# Developer quality shortcuts
# ---------------------------------------------------------------------------

quick:
	pytest -q

# Full unit-test run incl. coverage gate (≥ 85 %)

test:
	pytest --cov=graph_heal --cov-report=term-missing

# Heavy stress-scenario capture + evaluation + comparison plots

stress:
	PYTHONPATH=. graph-heal/run_capture_and_eval.sh --mode stress --plot 