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
    fh2_api_token: str
    fh2_upstream_verify_tls: bool

    @property
    def fh2_configured(self) -> bool:
        return bool(self.fh2_upstream_base_url)

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
            fh2_api_token=os.getenv("FH2_API_TOKEN", "").strip(),
            fh2_upstream_verify_tls=_as_bool(
                os.getenv("FH2_UPSTREAM_VERIFY_TLS", "true")
            ),
        )
