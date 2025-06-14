import networkx as nx
import importlib, pathlib, sys

# Guarantee project root is on sys.path
ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Dynamically resolve ServiceGraph implementation
ServiceGraph = importlib.import_module("graph_heal.service_graph").ServiceGraph  # type: ignore[attr-defined]


def test_circular_dependency_detection():
    sg = ServiceGraph()
    sg.add_service("A")
    sg.add_service("B")
    sg.add_service("C")
    sg.add_dependency("A", "B")
    sg.add_dependency("B", "C")
    sg.add_dependency("C", "A")  # Introduce cycle

    cycles = list(nx.simple_cycles(sg.graph))
    assert any(set(cycle) == {"A", "B", "C"} for cycle in cycles) 