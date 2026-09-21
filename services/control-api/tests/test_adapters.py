import asyncio

import httpx

from app.adapters.dji_cloud_api import DJICloudAPIAdapter
from app.adapters.fh2_openapi import FH2OpenAPIClient
from app.config import Settings


def test_dji_camera_paths_are_normalized_from_official_capacity_shape() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/manage/api/v1/live/capacity"
        assert request.headers["x-auth-token"] == "cloud-token"
        return httpx.Response(
            200,
            json={
                "code": 0,
                "data": [
                    {
                        "sn": "DRONE1",
                        "name": "Aircraft",
                        "cameras_list": [
                            {
                                "name": "Camera",
                                "index": "67-0-0",
                                "videos_list": [
                                    {
                                        "index": "normal-0",
                                        "type": "normal",
                                        "switch_video_types": ["wide", "zoom", "ir"],
                                    }
                                ],
                            }
                        ],
                    }
                ],
            },
        )

    settings = Settings(
        dji_cloud_api_base_url="https://cloud.example",
        dji_cloud_api_access_token="cloud-token",
    )
    adapter = DJICloudAPIAdapter(settings, transport=httpx.MockTransport(handler))

    paths = asyncio.run(adapter.camera_paths())

    assert len(paths) == 1
    assert paths[0].payload_index == "67-0-0"
    assert paths[0].video_id == "DRONE1/67-0-0/normal-0"
    assert paths[0].switchable_video_types == ["wide", "zoom", "ir"]


def test_dji_camera_paths_use_normal_fallback_when_video_list_is_empty() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "code": 0,
                "data": [
                    {
                        "sn": "DRONE2",
                        "cameras_list": [
                            {"index": "66-0-0", "videos_list": []}
                        ],
                    }
                ],
            },
        )

    settings = Settings(
        dji_cloud_api_base_url="https://cloud.example",
        dji_cloud_api_access_token="cloud-token",
    )
    adapter = DJICloudAPIAdapter(settings, transport=httpx.MockTransport(handler))
    path = asyncio.run(adapter.camera_paths())[0]

    assert path.video_id == "DRONE2/66-0-0/normal-0"
    assert path.fallback_video_index is True


def test_fh2_devices_use_v2_headers_and_repeated_airport_classes() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/organizations/org-1/manage-devices")
        assert request.headers["X-User-Token"] == "fh2-token"
        assert request.headers["X-Project-Uuid"] == "project-1"
        assert request.url.params.get_list("device_model_class") == [
            "airport",
            "base_station",
        ]
        return httpx.Response(200, json={"code": 0, "data": {"list": []}})

    settings = Settings(
        fh2_enabled=True,
        fh2_base_url="https://fh2.example",
        fh2_org_id="org-1",
        fh2_project_id="project-1",
        fh2_user_token="fh2-token",
    )
    client = FH2OpenAPIClient(settings, transport=httpx.MockTransport(handler))

    result = asyncio.run(client.list_devices("airport"))

    assert result == {"list": []}


def test_fh2_waylines_use_size_parameter() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.params["page"] == "2"
        assert request.url.params["size"] == "25"
        return httpx.Response(200, json={"code": 0, "data": {"list": []}})

    settings = Settings(
        fh2_enabled=True,
        fh2_base_url="https://fh2.example",
        fh2_org_id="org-1",
        fh2_project_id="project-1",
        fh2_user_token="fh2-token",
    )
    client = FH2OpenAPIClient(settings, transport=httpx.MockTransport(handler))

    result = asyncio.run(client.list_waylines(page=2, page_size=25))

    assert result == {"list": []}


def test_dji_bootstrap_marks_tls_transport() -> None:
    settings = Settings(
        mqtt_public_host="m4.example",
        mqtt_public_port=8883,
        mqtt_public_tls=True,
    )
    adapter = DJICloudAPIAdapter(settings)

    bootstrap = adapter.bootstrap_descriptor()

    assert bootstrap["mqtt"]["host"] == "m4.example"
    assert bootstrap["mqtt"]["port"] == 8883
    assert bootstrap["mqtt"]["tls"] is True
    assert bootstrap["mqtt"]["password_in_response"] is False
