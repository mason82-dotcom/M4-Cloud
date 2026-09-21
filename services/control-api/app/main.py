from __future__ import annotations

import os
import socket
from dataclasses import dataclass

from fastapi import FastAPI, Response, status

APP_NAME = "M4-Cloud Control API"
APP_VERSION = "1.0.0"


@dataclass(frozen=True)
class Settings:
    postgres_host: str
    postgres_port: int
    mqtt_host: str
    mqtt_port: int
    fh2_upstream_base_url: str
    fh2_upstream_verify_tls: bool

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            postgres_host=os.getenv("POSTGRES_HOST", "postgres"),
            postgres_port=int(os.getenv("POSTGRES_PORT", "5432")),
            mqtt_host=os.getenv("MQTT_HOST", "mqtt"),
            mqtt_port=int(os.getenv("MQTT_PORT", "1883")),
            fh2_upstream_base_url=os.getenv("FH2_UPSTREAM_BASE_URL", "").strip(),
            fh2_upstream_verify_tls=os.getenv(
                "FH2_UPSTREAM_VERIFY_TLS", "true"
            ).lower()
            in {"1", "true", "yes", "on"},
        )


def tcp_reachable(host: str, port: int, timeout: float = 1.0) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "control-api", "version": APP_VERSION}


@app.get("/ready")
def ready(response: Response) -> dict[str, object]:
    settings = Settings.from_env()
    dependencies = {
        "postgres": tcp_reachable(settings.postgres_host, settings.postgres_port),
        "mqtt": tcp_reachable(settings.mqtt_host, settings.mqtt_port),
    }
    is_ready = all(dependencies.values())
    if not is_ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return {"ready": is_ready, "dependencies": dependencies}


@app.get("/api/v1/system/status")
def system_status() -> dict[str, object]:
    settings = Settings.from_env()
    return {
        "service": "m4-cloud",
        "version": APP_VERSION,
        "fh2_upstream": {
            "configured": bool(settings.fh2_upstream_base_url),
            "verify_tls": settings.fh2_upstream_verify_tls,
        },
        "integration": {
            "mqtt": {"host": settings.mqtt_host, "port": settings.mqtt_port},
            "https": True,
            "websocket_proxy": True,
        },
    }
