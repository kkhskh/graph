from graph_heal.service_graph import ServiceGraph

def test_flip_remaining_branches():
    sg = ServiceGraph()
    sg.add_service("s1")
    sg.add_service("s2")
    sg.add_dependency("s1", "s2")

    # Feed correlated CPU usage so correlation path executes
    for cpu1, cpu2 in [(10, 20), (20, 40), (30, 60)]:
        sg.update_metrics("s1", {"service_cpu_usage": cpu1})
        sg.update_metrics("s2", {"service_cpu_usage": cpu2})

    # Hit both paths in dependency_strength
    assert sg.dependency_strength("s1", "s2") > 0
    assert sg.dependency_strength("s1", "nonexistent") == 0

    # get_latest_metrics and root-cause on unknown service to flip missing branches
    assert sg.get_latest_metrics("ghost") is None
    sg.get_root_cause("s1") 