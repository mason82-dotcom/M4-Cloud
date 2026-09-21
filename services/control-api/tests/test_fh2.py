import asyncio

import httpx
import pytest

from app.config import Settings
from app.fh2 import FH2APIError, FH2Client, FH2ConfigurationError


def make_settings(**overrides):
    values = {
        "postgres_host": "postgres",
        "postgres_port": 5432,
        "postgres_db": "m4cloud",
        "postgres_user": "m4cloud",
        "postgres_password": "secret",
        "mqtt_host": "mqtt",
        "mqtt_port": 1883,
        "dji_mqtt_topics": ("m4/fh2/#",),
        "fh2_upstream_base_url": "https://fh2.example.local",
        "fh2_user_token": "test-user-token",
        "fh2_org_uuid": "org-123",
        "fh2_project_uuid": "project-456",
        "fh2_language": "zh",
        "fh2_upstream_verify_tls": True,
        "fh2_timeout_seconds": 5.0,
        "dji_cloud_api_base_url": "",
        "dji_cloud_api_token": "",
        "dji_cloud_api_verify_tls": True,
        "dji_cloud_api_timeout_seconds": 5.0,
    }
    values.update(overrides)
    return Settings(**values)


def test_devices_use_official_v2_path_and_headers() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == (
            "/openapi/v2.0/manage/api/v1/organizations/org-123/manage-devices"
        )
        assert request.headers["X-User-Token"] == "test-user-token"
        assert request.headers["X-Project-Uuid"] == "project-456"
        assert request.headers["X-Language"] == "zh"
        assert request.headers.get("Authorization") is None
        assert request.headers.get("X-Request-Id")
        assert request.url.params.get_list("device_model_class") == [
            "airport",
            "base_station",
        ]
        assert request.url.params["page"] == "2"
        assert request.url.params["page_size"] == "25"
        return httpx.Response(
            200,
            json={"code": 0, "message": "", "data": {"list": [{"device_sn": "SN1"}]}},
        )

    client = FH2Client(make_settings(), transport=httpx.MockTransport(handler))
    result = asyncio.run(client.list_devices(device_class="airport", page=2, page_size=25))
    assert result["list"][0]["device_sn"] == "SN1"


def test_business_error_is_not_treated_as_success() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"code": 230001, "message": "permission denied", "data": None},
        )

    client = FH2Client(make_settings(), transport=httpx.MockTransport(handler))

    with pytest.raises(FH2APIError) as exc_info:
        asyncio.run(client.list_devices())

    assert exc_info.value.http_status == 200
    assert exc_info.value.business_code == 230001
    assert "permission denied" in str(exc_info.value)


def test_waylines_require_project_and_send_project_header() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == (
            "/openapi/v2.0/wayline/api/v1/workspaces/project-456/web-waylines"
        )
        assert request.headers["X-Project-Uuid"] == "project-456"
        assert request.url.params["page"] == "1"
        assert request.url.params["size"] == "100"
        return httpx.Response(200, json={"code": 0, "data": {"list": []}})

    client = FH2Client(make_settings(), transport=httpx.MockTransport(handler))
    assert asyncio.run(client.list_waylines()) == {"list": []}

    missing_project = FH2Client(
        make_settings(fh2_project_uuid=""),
        transport=httpx.MockTransport(handler),
    )
    with pytest.raises(FH2ConfigurationError):
        asyncio.run(missing_project.list_waylines())


def test_flight_tasks_encode_repeated_sn_brackets() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == (
            "/openapi/v2.0/task/api/v2/workspaces/project-456/flight-tasks"
        )
        assert request.url.params.get_list("sn[]") == ["DOCK-A", "DOCK-B"]
        assert request.url.params["flight_task_status"] == "1"
        return httpx.Response(200, json={"code": 0, "data": {"list": []}})

    client = FH2Client(make_settings(), transport=httpx.MockTransport(handler))
    result = asyncio.run(
        client.list_flight_tasks(
            flight_task_status=1,
            sns=["DOCK-A", "DOCK-B"],
        )
    )
    assert result == {"list": []}


def test_probe_requires_org_uuid_before_calling_official_endpoint() -> None:
    client = FH2Client(make_settings(fh2_org_uuid=""))
    result = asyncio.run(client.probe())

    assert result.reachable is False
    assert result.authenticated is False
    assert result.reason == "org_uuid_missing"
