from importlib import import_module

gh_mod = import_module("graph_heal.graph_heal")
GraphHeal = gh_mod.GraphHeal  # type: ignore[attr-defined]


def test_graphheal_cycle():
    gh = GraphHeal()
    gh.add_service("front")
    gh.add_service("db", dependencies=["front"])

    for _ in range(5):
        gh.update_metrics("front", {"cpu_usage": 5})
        gh.update_metrics("db", {"cpu_usage": 10})

    gh.update_metrics("front", {"cpu_usage": 90})  # spike

    if hasattr(gh, "run_detection_cycle"):
        gh.run_detection_cycle()
    else:
        for svc in gh.services.values():
            gh._handle_anomalies(svc.service_id, gh._detect_anomalies(svc))  # type: ignore[attr-defined]

    assert gh.propagation_history

    # Add orchestrator test
    # ... 