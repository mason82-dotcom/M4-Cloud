from __future__ import annotations

from typing import Any
from uuid import uuid4

import httpx

from app.config import Settings


class FH2NotConfigured(RuntimeError):
    pass


class FH2OpenAPIClient:
    """Schmaler Adapter für DJI FlightHub 2 OpenAPI V2."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    @property
    def configured(self) -> bool:
        s = self.settings
        return bool(
            s.fh2_enabled
            and s.fh2_base_url
            and s.fh2_org_id
            and s.fh2_project_id
            and s.fh2_user_token
        )

    def _headers(self) -> dict[str, str]:
        if not self.configured:
            raise FH2NotConfigured("FH2 OpenAPI V2 ist nicht vollständig konfiguriert")
        return {
            "x-user-token": self.settings.fh2_user_token,
            "X-Project-Uuid": self.settings.fh2_project_id,
            "X-Request-Id": str(uuid4()),
            "X-Language": "en",
        }

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
    ) -> Any:
        base_url = self.settings.fh2_base_url.rstrip("/")
        async with httpx.AsyncClient(
            base_url=base_url,
            headers=self._headers(),
            verify=self.settings.fh2_verify_tls,
            timeout=15.0,
        ) as client:
            response = await client.request(method, path, params=params, json=json)
            response.raise_for_status()
            payload = response.json()
            if isinstance(payload, dict) and payload.get("code") not in (None, 0):
                raise RuntimeError(payload.get("message") or f"FH2 API Fehler {payload.get('code')}")
            return payload

    async def list_devices(self, device_model_class: str = "drone") -> Any:
        return await self._request(
            "GET",
            f"/openapi/v2.0/manage/api/v1/organizations/{self.settings.fh2_org_id}/manage-devices",
            params={"device_model_class": device_model_class, "page": 1, "page_size": 100},
        )

    async def list_flight_tasks(self) -> Any:
        return await self._request(
            "GET",
            f"/openapi/v2.0/task/api/v2/workspaces/{self.settings.fh2_project_id}/flight-tasks",
        )

    async def list_waylines(self) -> Any:
        return await self._request(
            "GET",
            f"/openapi/v2.0/wayline/api/v1/workspaces/{self.settings.fh2_project_id}/web-waylines",
        )
