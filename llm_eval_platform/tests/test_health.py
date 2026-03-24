from fastapi.testclient import TestClient

from llm_eval_platform.api.main import app

client = TestClient(app)


def test_liveness() -> None:
    response = client.get("/health/live")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_readiness_success(monkeypatch) -> None:
    monkeypatch.setattr("llm_eval_platform.api.main.check_database_health", lambda: True)
    monkeypatch.setattr("llm_eval_platform.api.main.check_redis_health", lambda: True)

    response = client.get("/health/ready")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ready",
        "services": {"database": True, "redis": True},
    }


def test_readiness_failure(monkeypatch) -> None:
    monkeypatch.setattr("llm_eval_platform.api.main.check_database_health", lambda: True)
    monkeypatch.setattr("llm_eval_platform.api.main.check_redis_health", lambda: False)

    response = client.get("/health/ready")

    assert response.status_code == 503
    assert response.json() == {
        "status": "not_ready",
        "services": {"database": True, "redis": False},
    }

def test_prometheus_metrics_endpoint() -> None:
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "http_requests_total" in response.text