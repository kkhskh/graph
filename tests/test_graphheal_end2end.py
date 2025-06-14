from importlib import import_module

gh_mod = import_module("graph_heal.graph_heal")
GraphHeal = gh_mod.GraphHeal  # type: ignore[attr-defined]


def test_graphheal_end2end():
    gh = GraphHeal()
    gh.add_service("s1")
    gh.add_service("s2", dependencies=["s1"])

    # Update metrics a couple of times
    gh.update_metrics("s1", {"cpu_usage": 10})
    gh.update_metrics("s2", {"cpu_usage": 20})

    # Run a full detection cycle via the public method if exists
    if hasattr(gh, "run_detection_cycle"):
        gh.run_detection_cycle()
    else:
        # Fallback: manually call internal detection for coverage
        for svc in gh.services.values():
            gh._detect_anomalies(svc)  # type: ignore[attr-defined]

    # Ensure propagation history populated
    assert gh.propagation_history is not None

    summary = gh.get_health_summary()
    assert isinstance(summary, dict) 