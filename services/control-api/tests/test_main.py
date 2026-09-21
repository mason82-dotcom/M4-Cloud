from fastapi.testclient import TestClient

from app import main
from app.config import Settings
from app.cloud_api import CameraPath


client = TestClient(main.app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "control-api",
        "version": "1.1.0",
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
        "profile": "privatization-openapi-v2",
        "organization_configured": False,
        "project_configured": False,
        "reachable": False,
        "authenticated": False,
        "http_status": None,
        "business_code": None,
        "reason": "base_url_missing",
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


def test_fh2_devices_route_is_read_only_proxy(monkeypatch) -> None:
    monkeypatch.setenv("FH2_UPSTREAM_BASE_URL", "https://fh2.example.local")
    monkeypatch.setenv("FH2_USER_TOKEN", "secret-token")
    monkeypatch.setenv("FH2_ORG_UUID", "org-123")

    async def fake_list_devices(self, *, device_class, page, page_size):
        assert device_class == "drone"
        assert page == 2
        assert page_size == 10
        return {"list": [{"device_sn": "ABC123"}], "total": 1}

    monkeypatch.setattr(main.FH2Client, "list_devices", fake_list_devices)

    response = client.get("/api/v1/fh2/devices?device_class=drone&page=2&page_size=10")

    assert response.status_code == 200
    assert response.json()["data"]["list"][0]["device_sn"] == "ABC123"
    assert "secret-token" not in response.text


def test_fh2_hms_rejects_invalid_window(monkeypatch) -> None:
    response = client.get(
        "/api/v1/fh2/hms?device_sn=ABC123&begin_time_ms=200&end_time_ms=100"
    )

    assert response.status_code == 400


def test_fh2_waylines_configuration_error_is_503(monkeypatch) -> None:
    monkeypatch.delenv("FH2_PROJECT_UUID", raising=False)
    monkeypatch.setenv("FH2_UPSTREAM_BASE_URL", "https://fh2.example.local")
    monkeypatch.setenv("FH2_USER_TOKEN", "secret-token")

    response = client.get("/api/v1/fh2/waylines")

    assert response.status_code == 503
    assert response.json()["detail"]["error"] == "fh2_not_configured"
    assert "secret-token" not in response.text


def test_camera_status_does_not_expose_cloud_api_secrets(monkeypatch) -> None:
    monkeypatch.setenv("DJI_CLOUD_API_BASE_URL", "https://cloud.example.local")
    monkeypatch.setenv("DJI_CLOUD_API_TOKEN", "camera-secret-token")

    response = client.get("/api/v1/cameras/status")

    assert response.status_code == 200
    assert response.json() == {
        "configured": True,
        "source": "dji-cloud-api-live-capacity",
        "endpoint": "/manage/api/v1/live/capacity",
        "read_only": True,
        "lyrebird": False,
    }
    assert "camera-secret-token" not in response.text
    assert "cloud.example.local" not in response.text


def test_camera_paths_route_returns_normalized_paths(monkeypatch) -> None:
    monkeypatch.setenv("DJI_CLOUD_API_BASE_URL", "https://cloud.example.local")
    monkeypatch.setenv("DJI_CLOUD_API_TOKEN", "camera-secret-token")

    async def fake_get_camera_paths(self):
        return [
            CameraPath(
                device_sn="1581ABC",
                device_name="Mavic 3T",
                camera_name="Mavic 3T",
                camera_index="67-0-0",
                video_index="normal-0",
                video_type="normal",
                switchable_video_types=("wide", "zoom", "ir"),
                video_id="1581ABC/67-0-0/normal-0",
            )
        ]

    monkeypatch.setattr(main.DJICloudAPIClient, "get_camera_paths", fake_get_camera_paths)

    response = client.get("/api/v1/cameras/paths")

    assert response.status_code == 200
    assert response.json()["count"] == 1
    assert response.json()["paths"][0]["video_id"] == "1581ABC/67-0-0/normal-0"
    assert response.json()["paths"][0]["switchable_video_types"] == [
        "wide",
        "zoom",
        "ir",
    ]
    assert "camera-secret-token" not in response.text


def test_camera_telemetry_route_returns_latest_dji_values(monkeypatch) -> None:
    monkeypatch.setattr(
        main,
        "recent_events",
        lambda limit: [
            {
                "source": "mqtt",
                "topic": "thing/product/1581ABC/osd",
                "payload": {
                    "timestamp": 1790013000123,
                    "data": {
                        "cameras": [
                            {
                                "payload_index": "67-0-0",
                                "camera_mode": 0,
                                "recording_state": 1,
                                "zoom_factor": 3.5,
                            }
                        ],
                        "67-0-0": {
                            "payload_index": "67-0-0",
                            "gimbal_pitch": -45.0,
                            "gimbal_roll": 0.0,
                            "gimbal_yaw": 12.0,
                        },
                    },
                },
            }
        ],
    )

    response = client.get("/api/v1/cameras/telemetry?limit=25")

    assert response.status_code == 200
    payload = response.json()
    assert payload["source"] == "dji-mqtt-events"
    assert payload["read_only"] is True
    assert payload["count"] == 1
    assert payload["telemetry"][0]["payload_index"] == "67-0-0"
    assert payload["telemetry"][0]["camera"]["zoom_factor"] == 3.5
    assert payload["telemetry"][0]["gimbal"]["gimbal_pitch"] == -45.0



def test_camera_paths_requires_cloud_api_configuration(monkeypatch) -> None:
    monkeypatch.delenv("DJI_CLOUD_API_BASE_URL", raising=False)
    monkeypatch.delenv("DJI_CLOUD_API_TOKEN", raising=False)

    response = client.get("/api/v1/cameras/paths")

    assert response.status_code == 503
    assert response.json()["detail"]["error"] == "dji_cloud_api_not_configured"


def _set_complete_dji_bootstrap(monkeypatch) -> None:
    values = {
        "DJI_CLOUD_API_ENABLED": "true",
        "DJI_BOOTSTRAP_TOKEN": "bootstrap-secret",
        "DJI_PLATFORM_NAME": "M4 Cloud",
        "DJI_WORKSPACE_ID": "e3dea0f5-37f2-4d79-ae58-490af3228069",
        "DJI_WORKSPACE_NAME": "M4 Workspace",
        "DJI_WORKSPACE_DESCRIPTION": "M4 DJI Cloud",
        "DJI_APP_ID": "app-id",
        "DJI_APP_KEY": "app-key",
        "DJI_APP_LICENSE": "license",
        "DJI_API_HOST": "https://m4.example",
        "DJI_API_TOKEN": "api-token",
        "DJI_WS_HOST": "wss://m4.example/ws/dji",
        "DJI_WS_TOKEN": "ws-token",
        "DJI_MQTT_EXTERNAL_HOST": "tcp://m4.example:1883",
        "DJI_MQTT_USERNAME": "dji-pilot",
        "DJI_MQTT_PASSWORD": "mqtt-password",
    }
    for key, value in values.items():
        monkeypatch.setenv(key, value)


def test_dji_cloud_status_disabled_by_default(monkeypatch) -> None:
    monkeypatch.delenv("DJI_CLOUD_API_ENABLED", raising=False)
    response = client.get("/api/v1/dji/cloud/status")
    assert response.status_code == 200
    assert response.json()["enabled"] is False
    assert response.json()["capabilities"]["drc"] is False


def test_dji_bootstrap_requires_token(monkeypatch) -> None:
    _set_complete_dji_bootstrap(monkeypatch)
    assert client.get("/api/v1/dji/cloud/bootstrap").status_code == 401


def test_dji_bootstrap_returns_pilot2_configuration(monkeypatch) -> None:
    _set_complete_dji_bootstrap(monkeypatch)
    response = client.get(
        "/api/v1/dji/cloud/bootstrap",
        headers={"X-M4-Bootstrap-Token": "bootstrap-secret"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["license"]["app_id"] == "app-id"
    assert payload["mqtt"]["username"] == "dji-pilot"
    assert payload["features"]["device_commands"] is False
    assert payload["features"]["drc"] is False
