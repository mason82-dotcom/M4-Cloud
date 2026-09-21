from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "control-api"


def test_system_keeps_dji_paths_separate() -> None:
    response = client.get("/api/v1/system")
    assert response.status_code == 200
    architecture = response.json()["architecture"]
    assert architecture["fh2_openapi_v2"] == "separate-adapter"
    assert architecture["dji_cloud_api"] == "separate-adapter"
    assert architecture["lyrebird"] == "disabled"
