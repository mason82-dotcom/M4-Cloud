from fastapi.testclient import TestClient

from app import main


client = TestClient(main.app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "control-api",
        "version": "1.0.0",
    }


def test_ready_when_dependencies_are_reachable(monkeypatch) -> None:
    monkeypatch.setattr(main, "tcp_reachable", lambda host, port: True)
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.json()["ready"] is True


def test_ready_when_dependency_is_unreachable(monkeypatch) -> None:
    calls = iter([True, False])
    monkeypatch.setattr(main, "tcp_reachable", lambda host, port: next(calls))
    response = client.get("/ready")
    assert response.status_code == 503
    assert response.json()["ready"] is False


def test_system_status_does_not_expose_secrets(monkeypatch) -> None:
    monkeypatch.setenv("POSTGRES_PASSWORD", "super-secret")
    monkeypatch.setenv("FH2_UPSTREAM_BASE_URL", "https://fh2.example.local")
    response = client.get("/api/v1/system/status")

    assert response.status_code == 200
    payload = response.json()
    assert payload["fh2_upstream"]["configured"] is True
    assert "super-secret" not in response.text
    assert "fh2.example.local" not in response.text
