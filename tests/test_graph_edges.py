from graph_heal.graph_analysis import ServiceGraph


def test_zero_edge_graph_correlation_nan():
    g = ServiceGraph()
    g.add_service("a")
    g.add_service("b")
    # No edges or metrics – correlation should be (0.0,1.0)
    corr, p = g.calculate_correlation("a", "b")
    assert corr == 0.0 and p == 1.0


def test_duplicate_edge_idempotent():
    g = ServiceGraph()
    g.add_service("a")
    g.add_service("b")
    g.add_dependency("a", "b")
    g.add_dependency("a", "b")  # duplicate
    paths = list(g.graph.edges())
    assert paths.count(("a", "b")) == 1  # only one edge stored 