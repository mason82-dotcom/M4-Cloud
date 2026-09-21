from __future__ import annotations

import os
import socket
from dataclasses import dataclass

APP_NAME = "M4-Cloud Control API"
APP_VERSION = "1.0.0"


def _as_bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    postgres_host: str
    postgres_port: int
    postgres_db: str
    postgres_user: str
    postgres_password: str
    mqtt_host: str
    mqtt_port: int
    dji_mqtt_topics: tuple[str, ...]
    fh2_upstream_base_url: str
    fh2_user_token: str
    fh2_org_uuid: str
    fh2_project_uuid: str
    fh2_language: str
    fh2_upstream_verify_tls: bool
    fh2_timeout_seconds: float

    @property
    def fh2_base_configured(self) -> bool:
        return bool(self.fh2_upstream_base_url)

    @property
    def fh2_credentials_configured(self) -> bool:
        return bool(self.fh2_user_token)

    @property
    def fh2_configured(self) -> bool:
        """Minimum configuration required for authenticated FH2 OpenAPI calls."""
        return self.fh2_base_configured and self.fh2_credentials_configured

    @property
    def fh2_api_token(self) -> str:
        """Backward-compatible alias for pre-V2 code.

        New code must use fh2_user_token because DJI OpenAPI V2 expects
        X-User-Token rather than Authorization: Bearer.
        """
        return self.fh2_user_token

    @property
    def postgres_dsn(self) -> str:
        return (
            f"host={self.postgres_host} port={self.postgres_port} "
            f"dbname={self.postgres_db} user={self.postgres_user} "
            f"password={self.postgres_password}"
        )

    def mqtt_reachable(self, timeout: float = 1.0) -> bool:
        try:
            with socket.create_connection((self.mqtt_host, self.mqtt_port), timeout=timeout):
                return True
        except OSError:
            return False

    @classmethod
    def from_env(cls) -> "Settings":
        topics = tuple(
            topic.strip()
            for topic in os.getenv("DJI_MQTT_TOPICS", "m4/fh2/#").split(",")
            if topic.strip()
        )

        # FH2_API_TOKEN was used by M4 V1.0 before the official OpenAPI V2
        # authentication contract was integrated. Keep it as a migration
        # fallback, but prefer FH2_USER_TOKEN.
        user_token = os.getenv("FH2_USER_TOKEN", "").strip()
        if not user_token:
            user_token = os.getenv("FH2_API_TOKEN", "").strip()

        language = os.getenv("FH2_LANGUAGE", "zh").strip().lower() or "zh"
        if language not in {"zh", "en"}:
            language = "zh"

        return cls(
            postgres_host=os.getenv("POSTGRES_HOST", "postgres"),
            postgres_port=int(os.getenv("POSTGRES_PORT", "5432")),
            postgres_db=os.getenv("POSTGRES_DB", "m4cloud"),
            postgres_user=os.getenv("POSTGRES_USER", "m4cloud"),
            postgres_password=os.getenv("POSTGRES_PASSWORD", ""),
            mqtt_host=os.getenv("MQTT_HOST", "mqtt"),
            mqtt_port=int(os.getenv("MQTT_PORT", "1883")),
            dji_mqtt_topics=topics,
            fh2_upstream_base_url=os.getenv("FH2_UPSTREAM_BASE_URL", "").strip().rstrip("/"),
            fh2_user_token=user_token,
            fh2_org_uuid=os.getenv("FH2_ORG_UUID", "").strip(),
            fh2_project_uuid=os.getenv("FH2_PROJECT_UUID", "").strip(),
            fh2_language=language,
            fh2_upstream_verify_tls=_as_bool(
                os.getenv("FH2_UPSTREAM_VERIFY_TLS", "true")
            ),
            fh2_timeout_seconds=float(os.getenv("FH2_TIMEOUT_SECONDS", "15")),
        )
