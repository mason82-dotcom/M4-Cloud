from __future__ import annotations

from typing import Any
from uuid import uuid4

import httpx

from app.config import Settings


class FH2Error(RuntimeError):
    pass


class FH2NotConfigured(FH2Error):
    pass


class FH2OpenAPIClient:
    """Read-only adapter for DJI FlightHub 2 OpenAPI V2."""

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
        return self.settings.fh2_enabled

    @property
    def base_configured(self) -> bool:
        s = self.settings
        return bool(s.fh2_enabled and s.fh2_base_url and s.fh2_user_token)

    @property
    def organization_configured(self) -> bool:
        return bool(self.base_configured and self.settings.fh2_org_id)

    @property
    def project_configured(self) -> bool:
        return bool(self.base_configured and self.settings.fh2_project_id)

    @property
    def configured(self) -> bool:
        return self.organization_configured and self.project_configured

    def _headers(self) -> dict[str, str]:
        if not self.base_configured:
            raise FH2NotConfigured(
                "FH2 OpenAPI V2 ist nicht vollständig mit URL und X-User-Token konfiguriert"
            )
        headers = {
            "X-User-Token": self.settings.fh2_user_token,
            "X-Request-Id": str(uuid4()),
            "X-Language": "en",
            "Accept": "application/json",
        }
        if self.settings.fh2_project_id:
            headers["X-Project-Uuid"] = self.settings.fh2_project_id
        return headers

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: list[tuple[str, Any]] | dict[str, Any] | None = None,
    ) -> Any:
        try:
            async with httpx.AsyncClient(
                base_url=self.settings.fh2_base_url.rstrip("/"),
                headers=self._headers(),
                verify=self.settings.fh2_verify_tls,
                timeout=self.settings.fh2_timeout_seconds,
                follow_redirects=False,
                transport=self.transport,
            ) as client:
                response = await client.request(method, path, params=params)
        except httpx.HTTPError as exc:
            raise FH2Error(exc.__class__.__name__) from exc

        if response.status_code < 200 or response.status_code >= 300:
            raise FH2Error(f"FH2 OpenAPI HTTP {response.status_code}")

        payload = response.json()
        if isinstance(payload, dict) and payload.get("code") not in (None, 0, "0"):
            raise FH2Error(
                payload.get("message") or f"FH2 API Fehler {payload.get('code')}"
            )
        if isinstance(payload, dict) and "data" in payload:
            return payload["data"]
        return payload

    async def list_devices(
        self,
        device_model_class: str = "drone",
        *,
        page: int = 1,
        page_size: int = 100,
    ) -> Any:
        if not self.organization_configured:
            raise FH2NotConfigured("FH2_ORG_ID fehlt")
        classes = (
            ["airport", "base_station"]
            if device_model_class == "airport"
            else [device_model_class]
        )
        params: list[tuple[str, Any]] = [
            ("device_model_class", value) for value in classes
        ]
        params.extend([("page", page), ("page_size", page_size)])
        return await self._request(
            "GET",
            f"/openapi/v2.0/manage/api/v1/organizations/{self.settings.fh2_org_id}/manage-devices",
            params=params,
        )

    async def list_flight_tasks(
        self,
        *,
        page: int = 1,
        page_size: int = 50,
    ) -> Any:
        if not self.project_configured:
            raise FH2NotConfigured("FH2_PROJECT_ID fehlt")
        return await self._request(
            "GET",
            f"/openapi/v2.0/task/api/v2/workspaces/{self.settings.fh2_project_id}/flight-tasks",
            params={"page": page, "page_size": page_size},
        )

    async def list_waylines(
        self,
        *,
        page: int = 1,
        page_size: int = 100,
    ) -> Any:
        if not self.project_configured:
            raise FH2NotConfigured("FH2_PROJECT_ID fehlt")
        return await self._request(
            "GET",
            f"/openapi/v2.0/wayline/api/v1/workspaces/{self.settings.fh2_project_id}/web-waylines",
            params={"page": page, "size": page_size},
        )
