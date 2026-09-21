from __future__ import annotations

from typing import Any
from uuid import uuid4

import httpx

from app.config import Settings
from app.domain import CameraPath


class DJICloudAPIError(RuntimeError):
    pass


class DJICloudAPINotConfigured(DJICloudAPIError):
    pass


class DJICloudAPIAdapter:
    CAMERA_CAPACITY_PATH = "/manage/api/v1/live/capacity"

    def __init__(
        self,
        settings: Settings,
        *,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.settings = settings
        self.transport = transport

    @property
    def enabled(self) -> bool:
        return self.settings.dji_cloud_api_enabled

    @property
    def configured(self) -> bool:
        return bool(
            self.enabled
            and self.settings.dji_cloud_api_base_url
            and self.settings.dji_cloud_api_access_token
        )

    @property
    def mqtt_endpoint(self) -> str:
        return f"{self.settings.mqtt_public_host}:{self.settings.mqtt_public_port}"

    @property
    def mqtt_username(self) -> str:
        return self.settings.dji_mqtt_username

    @property
    def mqtt_tls_enabled(self) -> bool:
        return self.settings.mqtt_public_tls

    def bootstrap_descriptor(self) -> dict[str, object]:
        return {
            "mqtt": {
                "host": self.settings.mqtt_public_host,
                "port": self.settings.mqtt_public_port,
                "username": self.settings.dji_mqtt_username,
                "tls": self.settings.mqtt_public_tls,
                "password_in_response": False,
            },
            "topics": {
                "device_publish": [
                    "sys/product/+/status",
                    "thing/product/+/state",
                    "thing/product/+/osd",
                    "thing/product/+/requests",
                    "thing/product/+/events",
                    "thing/product/+/services_reply",
                    "thing/product/+/property/set_reply",
                ],
                "device_subscribe": [
                    "thing/product/+/services",
                    "thing/product/+/property/set",
                ],
                "drc_enabled": False,
            },
        }

    async def camera_paths(self) -> list[CameraPath]:
        payload = await self._request("GET", self.CAMERA_CAPACITY_PATH)
        return normalize_camera_paths(payload)

    async def _request(self, method: str, path: str) -> Any:
        if not self.configured:
            raise DJICloudAPINotConfigured(
                "DJI Cloud API ist für HTTP-Kameraerkennung nicht vollständig konfiguriert"
            )

        headers = {
            "x-auth-token": self.settings.dji_cloud_api_access_token,
            "X-Request-Id": str(uuid4()),
            "Accept": "application/json",
        }
        try:
            async with httpx.AsyncClient(
                base_url=self.settings.dji_cloud_api_base_url.rstrip("/"),
                headers=headers,
                verify=self.settings.dji_cloud_api_verify_tls,
                timeout=self.settings.dji_cloud_api_timeout_seconds,
                follow_redirects=False,
                transport=self.transport,
            ) as client:
                response = await client.request(method, path)
        except httpx.HTTPError as exc:
            raise DJICloudAPIError(exc.__class__.__name__) from exc

        if response.status_code < 200 or response.status_code >= 300:
            raise DJICloudAPIError(f"DJI Cloud API HTTP {response.status_code}")

        payload = response.json()
        if isinstance(payload, dict) and payload.get("code") not in (None, 0, "0"):
            raise DJICloudAPIError(
                payload.get("message") or f"DJI Cloud API Fehler {payload.get('code')}"
            )
        if isinstance(payload, dict) and "data" in payload:
            return payload["data"]
        return payload


def normalize_camera_paths(payload: Any) -> list[CameraPath]:
    if payload is None:
        return []
    if not isinstance(payload, list):
        raise DJICloudAPIError("live/capacity data muss eine Liste sein")

    result: list[CameraPath] = []
    for device in payload:
        if not isinstance(device, dict):
            continue
        device_sn = str(_field(device, "sn") or "").strip()
        if not device_sn:
            continue
        cameras = _field(
            device,
            "cameras_list",
            "camerasList",
            "camera_list",
            "cameraList",
        )
        if not isinstance(cameras, list):
            continue

        for camera in cameras:
            if not isinstance(camera, dict):
                continue
            payload_index = str(
                _field(camera, "index", "camera_index", "cameraIndex") or ""
            ).strip()
            if not payload_index:
                continue

            videos = _field(
                camera,
                "videos_list",
                "videosList",
                "video_list",
                "videoList",
            )
            if not isinstance(videos, list) or not videos:
                videos = [{"index": "normal-0", "type": "normal", "_fallback": True}]

            for video in videos:
                if not isinstance(video, dict):
                    continue
                video_type = str(
                    _field(video, "type", "video_type", "videoType") or "normal"
                ).strip().lower()
                video_index = str(
                    _field(video, "index", "video_index", "videoIndex")
                    or f"{video_type}-0"
                ).strip()
                switches = _field(
                    video,
                    "switch_video_types",
                    "switchVideoTypes",
                    "switchable_video_types",
                    "switchableVideoTypes",
                )
                switchable = (
                    [str(value).strip().lower() for value in switches if str(value).strip()]
                    if isinstance(switches, list)
                    else []
                )

                result.append(
                    CameraPath(
                        device_sn=device_sn,
                        device_name=_text(_field(device, "name")),
                        camera_name=_text(
                            _field(camera, "name", "camera_name", "cameraName")
                        ),
                        payload_index=payload_index,
                        video_index=video_index,
                        video_type=video_type,
                        switchable_video_types=switchable,
                        video_id=f"{device_sn}/{payload_index}/{video_index}",
                        fallback_video_index=bool(video.get("_fallback", False)),
                    )
                )
    return result


def _field(data: dict[str, Any], *names: str) -> Any:
    for name in names:
        if name in data:
            return data[name]
    return None


def _text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
