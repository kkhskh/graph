from graph_heal.health_manager import HealthManager

def test_health_penalties():
    hm = HealthManager()

    score, _ = hm.calculate_health_score({})
    assert score == 100

    bad_metrics = {"service_cpu_usage": 95, "service_memory_usage": 92, "latency_ms": 500}
    bad_score, _ = hm.calculate_health_score(bad_metrics)
    assert bad_score < 90

    sim = hm.simulate_recovery(bad_score, duration=5)
    assert sim[-1]["recovery_progress"] == 100 