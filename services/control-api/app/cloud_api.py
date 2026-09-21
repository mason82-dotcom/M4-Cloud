from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any

import httpx

from .config import Settings


@dataclass(frozen=True)
class CameraPath:
    device_sn: str
    device_name: str | None
    camera_name: str | None
    camera_index: str
    video_index: str
    video_type: str
    switchable_video_types: tuple[str, ...]
    video_id: str
    fallback_video_index: bool = False


class DJICloudAPIError(Exception):
    """Base error for the read-only DJI Cloud API adapter."""


class DJICloudAPIConfigurationError(DJICloudAPIError):
    """Local M4 configuration is incomplete."""


class DJICloudAPIConnectionError(DJICloudAPIError):
    """The configured DJI Cloud API server could not be reached."""


class DJICloudAPIUpstreamError(DJICloudAPIError):
    def __init__(
        self,
        message: str,
        *,
        http_status: int | None = None,
        business_code: int | str | None = None,
        request_id: str | None = None,
    ) -> None:
        super().__init__(message)
        self.http_status = http_status
        self.business_code = business_code
        self.request_id = request_id


class DJICloudAPIClient:
    """Read-only adapter for camera/live-capacity discovery.

    The endpoint and token header follow DJI's official Cloud API Demo:
    GET /manage/api/v1/live/capacity
    x-auth-token: <access_token>
    """

    CAMERA_CAPACITY_PATH = "/manage/api/v1/live/capacity"

    def __init__(
        self,
        settings: Settings,
        *,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.settings = settings
        self._transport = transport

    async def get_camera_paths(self) -> list[CameraPath]:
        payload = await self._request("GET", self.CAMERA_CAPACITY_PATH)
        return normalize_camera_paths(payload)

    async def _request(self, method: str, path: str) -> Any:
        if not self.settings.dji_cloud_api_base_url:
            raise DJICloudAPIConfigurationError(
                "DJI_CLOUD_API_BASE_URL is not configured"
            )
        if not self.settings.dji_cloud_api_token:
            raise DJICloudAPIConfigurationError(
                "DJI_CLOUD_API_TOKEN is not configured"
            )

        request_id = str(uuid.uuid4())
        headers = {
            "x-auth-token": self.settings.dji_cloud_api_token,
            "X-Request-Id": request_id,
            "Accept": "application/json",
            "User-Agent": "M4-Cloud/1.1",
        }

        try:
            async with httpx.AsyncClient(
                base_url=self.settings.dji_cloud_api_base_url,
                verify=self.settings.dji_cloud_api_verify_tls,
                timeout=self.settings.dji_cloud_api_timeout_seconds,
                follow_redirects=False,
                headers=headers,
                transport=self._transport,
            ) as client:
                response = await client.request(method, path)
        except httpx.HTTPError as exc:
            raise DJICloudAPIConnectionError(exc.__class__.__name__) from exc

        try:
            payload: Any = response.json() if response.content else {}
        except ValueError:
            payload = {"raw": response.text[:400]}

        if response.status_code >= 400:
            raise DJICloudAPIUpstreamError(
                _safe_message(payload) or f"HTTP {response.status_code}",
                http_status=response.status_code,
                request_id=request_id,
            )

        if isinstance(payload, dict):
            code = payload.get("code")
            if code not in (None, 0, "0"):
                raise DJICloudAPIUpstreamError(
                    _safe_message(payload) or "DJI Cloud API business error",
                    http_status=response.status_code,
                    business_code=code,
                    request_id=request_id,
                )
            if "data" in payload:
                return payload["data"]

        return payload


def normalize_camera_paths(payload: Any) -> list[CameraPath]:
    """Flatten DJI live-capacity data into stable M4 camera paths.

    DJI's official web demo consumes snake_case fields (cameras_list,
    videos_list, switch_video_types), while the Java DTOs use camelCase.
    M4 accepts both representations so it stays compatible with deployments
    using the same model through different serializers.
    """
    if payload is None:
        return []
    if not isinstance(payload, list):
        raise DJICloudAPIUpstreamError("live capacity data must be a list")

    paths: list[CameraPath] = []
    for device in payload:
        if not isinstance(device, dict):
            continue
        device_sn = str(_field(device, "sn") or "").strip()
        if not device_sn:
            continue
        device_name = _optional_text(_field(device, "name"))
        cameras = _field(device, "cameras_list", "camerasList", "camera_list", "cameraList")
        if not isinstance(cameras, list):
            continue

        for camera in cameras:
            if not isinstance(camera, dict):
                continue
            camera_index = str(
                _field(camera, "index", "camera_index", "cameraIndex") or ""
            ).strip()
            if not camera_index:
                continue
            camera_name = _optional_text(
                _field(camera, "name", "camera_name", "cameraName")
            )
            videos = _field(camera, "videos_list", "videosList", "video_list", "videoList")

            if not isinstance(videos, list) or not videos:
                video_index = "normal-0"
                paths.append(
                    CameraPath(
                        device_sn=device_sn,
                        device_name=device_name,
                        camera_name=camera_name,
                        camera_index=camera_index,
                        video_index=video_index,
                        video_type="normal",
                        switchable_video_types=(),
                        video_id=f"{device_sn}/{camera_index}/{video_index}",
                        fallback_video_index=True,
                    )
                )
                continue

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
                switch_values = _field(
                    video,
                    "switch_video_types",
                    "switchVideoTypes",
                    "switchable_video_types",
                    "switchableVideoTypes",
                )
                switches = tuple(
                    str(value).strip().lower()
                    for value in switch_values
                    if str(value).strip()
                ) if isinstance(switch_values, list) else ()

                paths.append(
                    CameraPath(
                        device_sn=device_sn,
                        device_name=device_name,
                        camera_name=camera_name,
                        camera_index=camera_index,
                        video_index=video_index,
                        video_type=video_type,
                        switchable_video_types=switches,
                        video_id=f"{device_sn}/{camera_index}/{video_index}",
                    )
                )

    return paths


def camera_path_to_dict(path: CameraPath) -> dict[str, Any]:
    return {
        "device_sn": path.device_sn,
        "device_name": path.device_name,
        "camera_name": path.camera_name,
        "camera_index": path.camera_index,
        "video_index": path.video_index,
        "video_type": path.video_type,
        "switchable_video_types": list(path.switchable_video_types),
        "video_id": path.video_id,
        "fallback_video_index": path.fallback_video_index,
    }


def _field(data: dict[str, Any], *names: str) -> Any:
    for name in names:
        if name in data:
            return data[name]
    return None


def _optional_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _safe_message(payload: Any) -> str:
    if not isinstance(payload, dict):
        return ""
    value = payload.get("message") or payload.get("msg") or payload.get("error")
    return "" if value is None else str(value)[:400]
