from fastapi.testclient import TestClient

from app import main
from app.config import Settings


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
    monkeypatch.setattr(main, "database_reachable", lambda: True)
    monkeypatch.setattr(Settings, "mqtt_reachable", lambda self: True)
    monkeypatch.setattr(
        main,
        "get_worker_heartbeat",
        lambda: {"service": "integration-worker", "fresh": True},
    )

    response = client.get("/ready")

    assert response.status_code == 200
    assert response.json() == {
        "ready": True,
        "dependencies": {
            "postgres": True,
            "mqtt": True,
            "integration_worker": True,
        },
    }


def test_ready_when_dependency_is_unreachable(monkeypatch) -> None:
    monkeypatch.setattr(main, "database_reachable", lambda: True)
    monkeypatch.setattr(Settings, "mqtt_reachable", lambda self: False)
    monkeypatch.setattr(
        main,
        "get_worker_heartbeat",
        lambda: {"service": "integration-worker", "fresh": True},
    )

    response = client.get("/ready")

    assert response.status_code == 503
    assert response.json()["ready"] is False
    assert response.json()["dependencies"]["mqtt"] is False


def test_system_status_does_not_expose_secrets(monkeypatch) -> None:
    monkeypatch.setenv("POSTGRES_PASSWORD", "super-secret")
    monkeypatch.setenv("FH2_API_TOKEN", "top-secret-token")
    monkeypatch.setenv("FH2_UPSTREAM_BASE_URL", "https://fh2.example.local")

    response = client.get("/api/v1/system/status")

    assert response.status_code == 200
    payload = response.json()
    assert payload["fh2_upstream"]["configured"] is True
    assert "super-secret" not in response.text
    assert "top-secret-token" not in response.text
    assert "fh2.example.local" not in response.text


def test_fh2_status_when_not_configured(monkeypatch) -> None:
    monkeypatch.delenv("FH2_UPSTREAM_BASE_URL", raising=False)

    response = client.get("/api/v1/fh2/status")

    assert response.status_code == 200
    assert response.json() == {
        "configured": False,
        "reachable": False,
        "reason": "not_configured",
    }


def test_ingest_event(monkeypatch) -> None:
    monkeypatch.setattr(main, "store_event", lambda source, topic, payload: 42)

    response = client.post(
        "/api/v1/events",
        json={"source": "fh2", "topic": "event/test", "payload": {"ok": True}},
    )

    assert response.status_code == 202
    assert response.json() == {"accepted": True, "id": 42}


def test_list_events_limit_validation() -> None:
    response = client.get("/api/v1/events?limit=501")
    assert response.status_code == 400


def test_websocket_ping() -> None:
    with client.websocket_connect("/ws/events") as websocket:
        websocket.send_text("ping")
        assert websocket.receive_json() == {"type": "pong"}


def test_metrics() -> None:
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "python_info" in response.text


def test_dji_cloud_status_disabled_by_default(monkeypatch) -> None:
    monkeypatch.delenv("DJI_CLOUD_API_ENABLED", raising=False)

    response = client.get("/api/v1/dji/cloud/status")

    assert response.status_code == 200
    payload = response.json()
    assert payload["enabled"] is False
    assert payload["subscriptions"] == []
    assert payload["capabilities"]["device_commands"] is False


def test_dji_cloud_status_enabled(monkeypatch) -> None:
    monkeypatch.setenv("DJI_CLOUD_API_ENABLED", "true")
    monkeypatch.setattr(Settings, "mqtt_reachable", lambda self: True)

    response = client.get("/api/v1/dji/cloud/status")

    assert response.status_code == 200
    payload = response.json()
    assert payload["enabled"] is True
    assert payload["mqtt_reachable"] is True
    assert "thing/product/+/osd" in payload["subscriptions"]
