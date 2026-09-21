from __future__ import annotations

from dataclasses import dataclass

import httpx

from .config import Settings


@dataclass(frozen=True)
class ProbeResult:
    reachable: bool
    http_status: int | None
    reason: str


class FH2Client:
    """Transport boundary for the licensed DJI FlightHub 2 upstream.

    No undocumented DJI endpoint paths are assumed here. Feature-specific
    OpenAPI methods can be added only when the target FH2 version's official
    OpenAPI definition is available.
    """

    def __init__(self, settings: Settings):
        self.settings = settings

    def _headers(self) -> dict[str, str]:
        headers = {"User-Agent": "M4-Cloud/1.0"}
        if self.settings.fh2_api_token:
            headers["Authorization"] = f"Bearer {self.settings.fh2_api_token}"
        return headers

    async def probe(self) -> ProbeResult:
        if not self.settings.fh2_configured:
            return ProbeResult(False, None, "not_configured")

        try:
            async with httpx.AsyncClient(
                verify=self.settings.fh2_upstream_verify_tls,
                timeout=5.0,
                follow_redirects=True,
                headers=self._headers(),
            ) as client:
                response = await client.get(self.settings.fh2_upstream_base_url)
            return ProbeResult(
                reachable=True,
                http_status=response.status_code,
                reason="reachable",
            )
        except httpx.HTTPError as exc:
            return ProbeResult(False, None, exc.__class__.__name__)
