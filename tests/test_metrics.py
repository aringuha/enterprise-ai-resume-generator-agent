from app.services.metrics import MetricsService


def test_metrics_records_successes_and_failures():
    service = MetricsService()

    service.record_success()
    service.record_failure()
    service.record_success()

    assert service.snapshot() == {
        "total_requests": 3,
        "successful_requests": 2,
        "failed_requests": 1,
        "crewai_enabled": True,
        "ollama_enabled": True,
    }


def test_metrics_snapshot_is_a_copy():
    service = MetricsService()
    snapshot = service.snapshot()

    snapshot["total_requests"] = 99

    assert service.snapshot()["total_requests"] == 0


def test_metrics_prometheus_snapshot_contains_counters():
    service = MetricsService()
    service.record_success()

    text = service.prometheus_snapshot()

    assert "resume_generator_requests_total 1" in text
    assert "resume_generator_requests_success_total 1" in text
