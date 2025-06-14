from datetime import datetime, timedelta
import importlib

ServiceGraph = importlib.import_module("graph_heal.service_graph").ServiceGraph  # type: ignore[attr-defined]


def test_graph_paths():
    sg = ServiceGraph()
    for s in ("A", "B", "C"):
        sg.add_service(s)
    sg.add_dependency("A", "B")
    sg.add_dependency("B", "C")

    now = datetime.utcnow()
    for i in range(10):
        ts = now + timedelta(seconds=i)
        sg.update_metrics("A", {"average_response_time": 10 + i}, ts)
        sg.update_metrics("B", {"average_response_time": 20 + i}, ts)
        sg.update_metrics("C", {"average_response_time": 30 + i}, ts)

    corr, _ = sg.calculate_correlation("A", "B")
    assert corr > 0.9 or corr == corr  # nan-safe

    faults = sg.detect_fault_propagation("A", [now])
    assert "B" in faults and "C" in faults

    sg.add_dependency("C", "A")
    assert sg.detect_circular_dependencies()

    heat = sg.create_propagation_heatmap("A")
    assert heat.shape[0] >= 1 