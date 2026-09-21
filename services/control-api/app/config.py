from __future__ import annotations

import os
import socket
from dataclasses import dataclass

APP_NAME = "M4-Cloud Control API"
APP_VERSION = "1.1.0"

DEFAULT_DJI_CLOUD_API_TOPICS = (
    "thing/product/+/osd",
    "thing/product/+/state",
    "thing/product/+/services_reply",
    "thing/product/+/events",
    "thing/product/+/requests",
    "thing/product/+/property/set_reply",
    "sys/product/+/status",
)


def _as_bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _as_csv(value: str) -> tuple[str, ...]:
    return tuple(item.strip() for item in value.split(",") if item.strip())


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
    dji_cloud_api_base_url: str
    dji_cloud_api_token: str
    dji_cloud_api_verify_tls: bool
    dji_cloud_api_timeout_seconds: float

    mqtt_username: str = "m4-worker"
    mqtt_password: str = ""
    dji_cloud_api_enabled: bool = False
    dji_cloud_api_topics: tuple[str, ...] = DEFAULT_DJI_CLOUD_API_TOPICS
    dji_bootstrap_token: str = ""
    dji_platform_name: str = "M4 Cloud"
    dji_workspace_id: str = ""
    dji_workspace_name: str = "M4 Workspace"
    dji_workspace_description: str = "M4 DJI Cloud"
    dji_app_id: str = ""
    dji_app_key: str = ""
    dji_app_license: str = ""
    dji_api_host: str = ""
    dji_api_token: str = ""
    dji_ws_host: str = ""
    dji_ws_token: str = ""
    dji_mqtt_external_host: str = ""
    dji_mqtt_username: str = "dji-pilot"
    dji_mqtt_password: str = ""

    @property
    def fh2_base_configured(self) -> bool:
        return bool(self.fh2_upstream_base_url)

    @property
    def fh2_credentials_configured(self) -> bool:
        return bool(self.fh2_user_token)

    @property
    def fh2_configured(self) -> bool:
        return self.fh2_base_configured and self.fh2_credentials_configured

    @property
    def fh2_api_token(self) -> str:
        return self.fh2_user_token

    @property
    def dji_cloud_api_configured(self) -> bool:
        return bool(self.dji_cloud_api_base_url and self.dji_cloud_api_token)

    @property
    def mqtt_subscriptions(self) -> tuple[str, ...]:
        topics = list(self.dji_mqtt_topics)
        if self.dji_cloud_api_enabled:
            topics.extend(self.dji_cloud_api_topics)
        return tuple(dict.fromkeys(topics))

    @property
    def dji_bootstrap_ready(self) -> bool:
        required = (
            self.dji_bootstrap_token,
            self.dji_workspace_id,
            self.dji_app_id,
            self.dji_app_key,
            self.dji_app_license,
            self.dji_api_host,
            self.dji_api_token,
            self.dji_ws_host,
            self.dji_ws_token,
            self.dji_mqtt_external_host,
            self.dji_mqtt_username,
            self.dji_mqtt_password,
        )
        return self.dji_cloud_api_enabled and all(required)

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
        user_token = os.getenv("FH2_USER_TOKEN", "").strip()
        if not user_token:
            user_token = os.getenv("FH2_API_TOKEN", "").strip()

        language = os.getenv("FH2_LANGUAGE", "zh").strip().lower() or "zh"
        if language not in {"zh", "en"}:
            language = "zh"

        worker_username = os.getenv(
            "MQTT_USERNAME",
            os.getenv("MQTT_WORKER_USERNAME", "m4-worker"),
        ).strip()
        worker_password = os.getenv(
            "MQTT_PASSWORD",
            os.getenv("MQTT_WORKER_PASSWORD", ""),
        )

        return cls(
            postgres_host=os.getenv("POSTGRES_HOST", "postgres"),
            postgres_port=int(os.getenv("POSTGRES_PORT", "5432")),
            postgres_db=os.getenv("POSTGRES_DB", "m4cloud"),
            postgres_user=os.getenv("POSTGRES_USER", "m4cloud"),
            postgres_password=os.getenv("POSTGRES_PASSWORD", ""),
            mqtt_host=os.getenv("MQTT_HOST", "mqtt"),
            mqtt_port=int(os.getenv("MQTT_PORT", "1883")),
            dji_mqtt_topics=_as_csv(os.getenv("DJI_MQTT_TOPICS", "m4/fh2/#")),
            fh2_upstream_base_url=os.getenv("FH2_UPSTREAM_BASE_URL", "").strip().rstrip("/"),
            fh2_user_token=user_token,
            fh2_org_uuid=os.getenv("FH2_ORG_UUID", "").strip(),
            fh2_project_uuid=os.getenv("FH2_PROJECT_UUID", "").strip(),
            fh2_language=language,
            fh2_upstream_verify_tls=_as_bool(os.getenv("FH2_UPSTREAM_VERIFY_TLS", "true")),
            fh2_timeout_seconds=float(os.getenv("FH2_TIMEOUT_SECONDS", "15")),
            dji_cloud_api_base_url=os.getenv("DJI_CLOUD_API_BASE_URL", "").strip().rstrip("/"),
            dji_cloud_api_token=os.getenv("DJI_CLOUD_API_TOKEN", "").strip(),
            dji_cloud_api_verify_tls=_as_bool(os.getenv("DJI_CLOUD_API_VERIFY_TLS", "true")),
            dji_cloud_api_timeout_seconds=float(os.getenv("DJI_CLOUD_API_TIMEOUT_SECONDS", "15")),
            mqtt_username=worker_username,
            mqtt_password=worker_password,
            dji_cloud_api_enabled=_as_bool(os.getenv("DJI_CLOUD_API_ENABLED", "false")),
            dji_cloud_api_topics=_as_csv(
                os.getenv("DJI_CLOUD_API_TOPICS", ",".join(DEFAULT_DJI_CLOUD_API_TOPICS))
            ),
            dji_bootstrap_token=os.getenv("DJI_BOOTSTRAP_TOKEN", "").strip(),
            dji_platform_name=os.getenv("DJI_PLATFORM_NAME", "M4 Cloud").strip(),
            dji_workspace_id=os.getenv("DJI_WORKSPACE_ID", "").strip(),
            dji_workspace_name=os.getenv("DJI_WORKSPACE_NAME", "M4 Workspace").strip(),
            dji_workspace_description=os.getenv("DJI_WORKSPACE_DESCRIPTION", "M4 DJI Cloud").strip(),
            dji_app_id=os.getenv("DJI_APP_ID", "").strip(),
            dji_app_key=os.getenv("DJI_APP_KEY", "").strip(),
            dji_app_license=os.getenv("DJI_APP_LICENSE", "").strip(),
            dji_api_host=os.getenv("DJI_API_HOST", "").strip().rstrip("/"),
            dji_api_token=os.getenv("DJI_API_TOKEN", "").strip(),
            dji_ws_host=os.getenv("DJI_WS_HOST", "").strip(),
            dji_ws_token=os.getenv("DJI_WS_TOKEN", "").strip(),
            dji_mqtt_external_host=os.getenv("DJI_MQTT_EXTERNAL_HOST", "").strip(),
            dji_mqtt_username=os.getenv("DJI_MQTT_USERNAME", "dji-pilot").strip(),
            dji_mqtt_password=os.getenv("DJI_MQTT_PASSWORD", ""),
        )
