import asyncio

import httpx
import pytest

from app.cloud_api import (
    DJICloudAPIClient,
    DJICloudAPIUpstreamError,
    normalize_camera_paths,
)
from app.config import Settings


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
        "fh2_upstream_base_url": "",
        "fh2_user_token": "",
        "fh2_org_uuid": "",
        "fh2_project_uuid": "",
        "fh2_language": "zh",
        "fh2_upstream_verify_tls": True,
        "fh2_timeout_seconds": 5.0,
        "dji_cloud_api_base_url": "https://cloud.example.local",
        "dji_cloud_api_token": "camera-token",
        "dji_cloud_api_verify_tls": True,
        "dji_cloud_api_timeout_seconds": 5.0,
    }
    values.update(overrides)
    return Settings(**values)


def test_reads_official_live_capacity_endpoint_and_auth_header() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/manage/api/v1/live/capacity"
        assert request.headers["x-auth-token"] == "camera-token"
        assert request.headers.get("X-Request-Id")
        return httpx.Response(
            200,
            json={
                "code": 0,
                "data": [
                    {
                        "sn": "1581ABC",
                        "name": "Mavic 3T",
                        "cameras_list": [
                            {
                                "name": "Mavic 3T",
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

    client = DJICloudAPIClient(
        make_settings(),
        transport=httpx.MockTransport(handler),
    )
    paths = asyncio.run(client.get_camera_paths())

    assert len(paths) == 1
    assert paths[0].video_id == "1581ABC/67-0-0/normal-0"
    assert paths[0].switchable_video_types == ("wide", "zoom", "ir")


def test_normalizer_accepts_java_camel_case_shape() -> None:
    paths = normalize_camera_paths(
        [
            {
                "sn": "DRONE-1",
                "name": "Aircraft",
                "camerasList": [
                    {
                        "name": "Payload",
                        "index": "53-0-0",
                        "videosList": [
                            {
                                "index": "thermal-0",
                                "type": "thermal",
                                "switchVideoTypes": [],
                            }
                        ],
                    }
                ],
            }
        ]
    )

    assert paths[0].camera_index == "53-0-0"
    assert paths[0].video_type == "thermal"
    assert paths[0].video_id == "DRONE-1/53-0-0/thermal-0"


def test_normalizer_uses_official_demo_normal_fallback_when_video_list_empty() -> None:
    paths = normalize_camera_paths(
        [
            {
                "sn": "DRONE-2",
                "cameras_list": [
                    {
                        "name": "Camera",
                        "index": "66-0-0",
                        "videos_list": [],
                    }
                ],
            }
        ]
    )

    assert paths[0].video_id == "DRONE-2/66-0-0/normal-0"
    assert paths[0].fallback_video_index is True


def test_business_error_is_rejected() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"code": 401, "message": "invalid token", "data": None},
        )

    client = DJICloudAPIClient(
        make_settings(),
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(DJICloudAPIUpstreamError) as exc_info:
        asyncio.run(client.get_camera_paths())

    assert exc_info.value.business_code == 401
    assert "invalid token" in str(exc_info.value)
