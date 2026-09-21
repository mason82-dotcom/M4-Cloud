from fastapi.testclient import TestClient

from app import main

client = TestClient(main.app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "control-api"


def test_ready_uses_real_dependency_results(monkeypatch) -> None:
    monkeypatch.setattr(main, "database_reachable", lambda settings: True)
    monkeypatch.setattr(main, "mqtt_reachable", lambda settings: True)

    response = client.get("/ready")

    assert response.status_code == 200
    assert response.json() == {
        "ready": True,
        "dependencies": {
            "postgres": True,
            "mqtt_authenticated": True,
        },
    }


def test_ready_returns_503_if_dependency_is_down(monkeypatch) -> None:
    monkeypatch.setattr(main, "database_reachable", lambda settings: True)
    monkeypatch.setattr(main, "mqtt_reachable", lambda settings: False)

    response = client.get("/ready")

    assert response.status_code == 503
    assert response.json()["ready"] is False


def test_system_keeps_dji_paths_separate_and_hides_secrets(monkeypatch) -> None:
    monkeypatch.setenv("FH2_USER_TOKEN", "fh2-secret")
    monkeypatch.setenv("DJI_CLOUD_API_ACCESS_TOKEN", "cloud-secret")
    main.get_settings.cache_clear()

    response = client.get("/api/v1/system")

    assert response.status_code == 200
    architecture = response.json()["architecture"]
    assert architecture["fh2_openapi_v2"] == "separate-adapter"
    assert architecture["dji_cloud_api"] == "separate-adapter"
    assert architecture["lyrebird"] == "disabled"
    assert "fh2-secret" not in response.text
    assert "cloud-secret" not in response.text

    main.get_settings.cache_clear()


def test_bootstrap_never_returns_mqtt_password() -> None:
    response = client.get("/api/v1/cloud/bootstrap")

    assert response.status_code == 200
    body = response.json()
    assert body["mqtt"]["password_in_response"] is False
    assert body["mqtt"]["tls"] is False
    assert "password" not in {
        key for key in body["mqtt"] if key != "password_in_response"
    }
    assert body["topics"]["drc_enabled"] is False


def test_camera_status_is_read_only() -> None:
    response = client.get("/api/v1/cameras/status")

    assert response.status_code == 200
    body = response.json()
    assert body["read_only"] is True
    assert body["lyrebird"] is False
