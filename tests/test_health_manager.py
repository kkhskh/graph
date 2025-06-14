from graph_heal.health_manager import HealthManager


def test_health_score_and_recovery():
    hm = HealthManager()

    # Healthy metrics give high score
    score, state = hm.calculate_health_score({
        "service_cpu_usage": 5,
        "service_memory_usage": 10,
        "service_response_time": 0.05,
    })
    assert state == "healthy"
    assert score > 75

    # Critical metrics drop the score dramatically
    bad_metrics = {
        "service_cpu_usage": 95,
        "service_memory_usage": 92,
        "service_response_time": 1.2,
    }
    bad_score, bad_state = hm.calculate_health_score(bad_metrics)
    assert bad_state in {"warning", "critical", "degraded"}
    assert bad_score < 75

    # Recovery time increases with health gap
    rec_short = hm.calculate_recovery_time(score)
    rec_long = hm.calculate_recovery_time(bad_score)
    assert rec_long > rec_short

    # Simulate recovery path – ensure monotonic progress of recovery_progress
    sim = hm.simulate_recovery(bad_score, duration=10)
    assert sim[0]["health_score"] <= sim[-1]["health_score"]
    assert sim[-1]["recovery_progress"] == 100

    # Health summary aggregation
    summary = hm.get_health_summary([bad_metrics, bad_metrics, bad_metrics])
    assert summary["critical_percent"] > 0 