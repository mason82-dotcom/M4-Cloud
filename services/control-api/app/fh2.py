from __future__ import annotations

import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

import httpx

from .config import Settings


@dataclass(frozen=True)
class ProbeResult:
    reachable: bool
    authenticated: bool
    http_status: int | None
    reason: str
    business_code: int | str | None = None


class FH2Error(Exception):
    """Base class for FlightHub 2 integration errors."""


class FH2ConfigurationError(FH2Error):
    """Local M4 configuration is incomplete for the requested operation."""


class FH2ConnectionError(FH2Error):
    """The configured FlightHub 2 server could not be reached."""


class FH2APIError(FH2Error):
    """FlightHub 2 rejected a request through HTTP or its business envelope."""

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


class FH2Client:
    """Read-only DJI FlightHub 2 Privatization OpenAPI V2 adapter.

    Endpoint paths implemented here are taken from DJI's official
    FlightHub-2-OpenAPI-V2-Demo. The transport intentionally exposes only
    read operations in this phase.
    """

    API_PROFILE = "privatization-openapi-v2"

    def __init__(
        self,
        settings: Settings,
        *,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.settings = settings
        self._transport = transport

    def _headers(self, *, require_project: bool = False) -> dict[str, str]:
        if not self.settings.fh2_user_token:
            raise FH2ConfigurationError("FH2_USER_TOKEN is not configured")
        if require_project and not self.settings.fh2_project_uuid:
            raise FH2ConfigurationError("FH2_PROJECT_UUID is not configured")

        headers = {
            "X-User-Token": self.settings.fh2_user_token,
            "X-Request-Id": str(uuid.uuid4()),
            "X-Language": self.settings.fh2_language,
            "Accept": "application/json",
            "User-Agent": "M4-Cloud/1.0",
        }
        if self.settings.fh2_project_uuid:
            headers["X-Project-Uuid"] = self.settings.fh2_project_uuid
        return headers

    def _base_url(self) -> str:
        if not self.settings.fh2_upstream_base_url:
            raise FH2ConfigurationError("FH2_UPSTREAM_BASE_URL is not configured")
        return self.settings.fh2_upstream_base_url

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | Sequence[tuple[str, Any]] | None = None,
        require_project: bool = False,
    ) -> Any:
        base_url = self._base_url()
        headers = self._headers(require_project=require_project)
        request_id = headers["X-Request-Id"]

        try:
            async with httpx.AsyncClient(
                base_url=base_url,
                verify=self.settings.fh2_upstream_verify_tls,
                timeout=self.settings.fh2_timeout_seconds,
                follow_redirects=False,
                headers=headers,
                transport=self._transport,
            ) as client:
                response = await client.request(method, path, params=params)
        except httpx.HTTPError as exc:
            raise FH2ConnectionError(exc.__class__.__name__) from exc

        try:
            payload: Any = response.json() if response.content else {}
        except ValueError:
            payload = {"raw": response.text[:400]}

        if response.status_code >= 400:
            message = _safe_message(payload) or f"HTTP {response.status_code}"
            raise FH2APIError(
                message,
                http_status=response.status_code,
                request_id=request_id,
            )

        if isinstance(payload, dict):
            code = payload.get("code")
            if code not in (None, 0, "0"):
                raise FH2APIError(
                    _safe_message(payload) or "FlightHub 2 business error",
                    http_status=response.status_code,
                    business_code=code,
                    request_id=request_id,
                )
            if "data" in payload:
                return payload["data"]

        return payload

    async def probe(self) -> ProbeResult:
        if not self.settings.fh2_upstream_base_url:
            return ProbeResult(False, False, None, "base_url_missing")
        if not self.settings.fh2_user_token:
            return ProbeResult(False, False, None, "user_token_missing")
        if not self.settings.fh2_org_uuid:
            return ProbeResult(False, False, None, "org_uuid_missing")

        try:
            await self.list_devices(device_class="airport", page=1, page_size=1)
            return ProbeResult(True, True, 200, "openapi_ok")
        except FH2APIError as exc:
            return ProbeResult(
                reachable=True,
                authenticated=False,
                http_status=exc.http_status,
                reason="upstream_rejected_request",
                business_code=exc.business_code,
            )
        except FH2ConnectionError as exc:
            return ProbeResult(False, False, None, str(exc))
        except FH2ConfigurationError as exc:
            return ProbeResult(False, False, None, str(exc))

    async def list_devices(
        self,
        *,
        device_class: str = "airport",
        page: int = 1,
        page_size: int = 200,
    ) -> Any:
        org_uuid = self.settings.fh2_org_uuid
        if not org_uuid:
            raise FH2ConfigurationError("FH2_ORG_UUID is not configured")

        classes: list[str]
        if device_class == "airport":
            # DJI's official V2 demo groups airports and base stations together.
            classes = ["airport", "base_station"]
        elif device_class in {"drone", "base_station"}:
            classes = [device_class]
        else:
            raise FH2ConfigurationError(
                "device_class must be airport, drone or base_station"
            )

        params: list[tuple[str, Any]] = [
            ("page", page),
            ("page_size", page_size),
        ]
        params.extend(("device_model_class", value) for value in classes)

        return await self._request(
            "GET",
            f"/openapi/v2.0/manage/api/v1/organizations/{org_uuid}/manage-devices",
            params=params,
        )

    async def list_hms(
        self,
        *,
        device_sns: Sequence[str],
        begin_time_ms: int,
        end_time_ms: int,
        page: int = 1,
        page_size: int = 20,
    ) -> Any:
        org_uuid = self.settings.fh2_org_uuid
        if not org_uuid:
            raise FH2ConfigurationError("FH2_ORG_UUID is not configured")

        unique_sns = list(dict.fromkeys(sn.strip() for sn in device_sns if sn.strip()))
        if not unique_sns:
            raise FH2ConfigurationError("at least one device serial number is required")

        params: list[tuple[str, Any]] = [
            ("begin_time", begin_time_ms),
            ("end_time", end_time_ms),
            ("language", self.settings.fh2_language),
            ("page", page),
            ("page_size", page_size),
        ]
        params.extend(("device_sn", sn) for sn in unique_sns)

        return await self._request(
            "GET",
            f"/openapi/v2.0/manage/api/v1/organizations/{org_uuid}/manage-devices/hms",
            params=params,
        )

    async def list_waylines(self, *, page: int = 1, page_size: int = 100) -> Any:
        project_uuid = self.settings.fh2_project_uuid
        if not project_uuid:
            raise FH2ConfigurationError("FH2_PROJECT_UUID is not configured")

        return await self._request(
            "GET",
            f"/openapi/v2.0/wayline/api/v1/workspaces/{project_uuid}/web-waylines",
            params={"page": page, "size": page_size},
            require_project=True,
        )

    async def list_flight_tasks(
        self,
        *,
        page: int = 1,
        page_size: int = 50,
        flight_task_status: int | None = None,
        sns: Sequence[str] = (),
    ) -> Any:
        project_uuid = self.settings.fh2_project_uuid
        if not project_uuid:
            raise FH2ConfigurationError("FH2_PROJECT_UUID is not configured")

        params: list[tuple[str, Any]] = [("page", page), ("page_size", page_size)]
        if flight_task_status is not None:
            params.append(("flight_task_status", flight_task_status))
        params.extend(("sn[]", sn.strip()) for sn in sns if sn.strip())

        return await self._request(
            "GET",
            f"/openapi/v2.0/task/api/v2/workspaces/{project_uuid}/flight-tasks",
            params=params,
            require_project=True,
        )


def _safe_message(payload: Any) -> str:
    if not isinstance(payload, dict):
        return ""
    value = payload.get("message") or payload.get("msg") or payload.get("error")
    if value is None:
        return ""
    return str(value)[:400]
