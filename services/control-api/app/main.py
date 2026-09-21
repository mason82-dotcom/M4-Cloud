from __future__ import annotations

import hmac
from contextlib import asynccontextmanager

from fastapi import FastAPI, Header, HTTPException, Response, WebSocket, WebSocketDisconnect, status
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from .config import APP_NAME, APP_VERSION, Settings
from .db import (
    database_reachable,
    ensure_schema,
    get_worker_heartbeat,
    recent_events,
    store_event,
)
from .fh2 import FH2Client
from .models import EventIn


@asynccontextmanager
async def lifespan(_: FastAPI):
    ensure_schema()
    yield


app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "control-api", "version": APP_VERSION}


@app.get("/ready")
def ready(response: Response) -> dict[str, object]:
    settings = Settings.from_env()
    postgres_ok = database_reachable()
    mqtt_ok = settings.mqtt_reachable()
    worker = get_worker_heartbeat()
    worker_ok = bool(worker and worker["fresh"])

    dependencies = {
        "postgres": postgres_ok,
        "mqtt": mqtt_ok,
        "integration_worker": worker_ok,
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
            "configured": settings.fh2_configured,
            "verify_tls": settings.fh2_upstream_verify_tls,
        },
        "dji_cloud_api": {
            "enabled": settings.dji_cloud_api_enabled,
            "bootstrap_ready": settings.dji_bootstrap_ready,
        },
        "integration": {
            "mqtt": {"host": settings.mqtt_host, "port": settings.mqtt_port},
            "https": True,
            "websocket": True,
            "event_persistence": True,
            "metrics": True,
        },
    }


@app.get("/api/v1/dji/cloud/status")
def dji_cloud_status() -> dict[str, object]:
    settings = Settings.from_env()
    subscriptions = (
        list(settings.dji_cloud_api_topics)
        if settings.dji_cloud_api_enabled
        else []
    )
    return {
        "enabled": settings.dji_cloud_api_enabled,
        "mqtt_reachable": (
            settings.mqtt_reachable() if settings.dji_cloud_api_enabled else False
        ),
        "bootstrap_ready": settings.dji_bootstrap_ready,
        "subscriptions": subscriptions,
        "capabilities": {
            "mqtt_ingest": settings.dji_cloud_api_enabled,
            "mqtt_authentication": True,
            "mqtt_acl": True,
            "pilot2_webview_bootstrap": settings.dji_bootstrap_ready,
            "device_commands": False,
            "drc": False,
        },
    }


@app.get("/api/v1/dji/cloud/bootstrap")
def dji_cloud_bootstrap(
    x_m4_bootstrap_token: str | None = Header(
        default=None,
        alias="X-M4-Bootstrap-Token",
    ),
) -> dict[str, object]:
    settings = Settings.from_env()
    if not settings.dji_cloud_api_enabled:
        raise HTTPException(status_code=503, detail="dji_cloud_api_disabled")
    if not settings.dji_bootstrap_ready:
        raise HTTPException(status_code=503, detail="dji_cloud_bootstrap_incomplete")
    if not x_m4_bootstrap_token or not hmac.compare_digest(
        x_m4_bootstrap_token,
        settings.dji_bootstrap_token,
    ):
        raise HTTPException(status_code=401, detail="invalid_bootstrap_token")

    return {
        "platform": {
            "name": settings.dji_platform_name,
        },
        "workspace": {
            "id": settings.dji_workspace_id,
            "name": settings.dji_workspace_name,
            "description": settings.dji_workspace_description,
        },
        "license": {
            "app_id": settings.dji_app_id,
            "app_key": settings.dji_app_key,
            "license": settings.dji_app_license,
        },
        "api": {
            "host": settings.dji_api_host,
            "token": settings.dji_api_token,
        },
        "websocket": {
            "host": settings.dji_ws_host,
            "token": settings.dji_ws_token,
        },
        "mqtt": {
            "host": settings.dji_mqtt_external_host,
            "username": settings.dji_mqtt_username,
            "password": settings.dji_mqtt_password,
        },
        "features": {
            "map": True,
            "tsa": True,
            "media": False,
            "mission": False,
            "device_commands": False,
            "drc": False,
        },
    }


@app.get("/api/v1/fh2/status")
async def fh2_status() -> dict[str, object]:
    settings = Settings.from_env()
    if not settings.fh2_configured:
        return {"configured": False, "reachable": False, "reason": "not_configured"}

    probe = await FH2Client(settings).probe()
    return {
        "configured": True,
        "reachable": probe.reachable,
        "http_status": probe.http_status,
        "reason": probe.reason,
    }


@app.post("/api/v1/events", status_code=status.HTTP_202_ACCEPTED)
def ingest_event(event: EventIn) -> dict[str, object]:
    event_id = store_event(
        source=event.source,
        topic=event.topic,
        payload=event.payload,
    )
    return {"accepted": True, "id": event_id}


@app.get("/api/v1/events")
def list_events(limit: int = 100) -> dict[str, object]:
    if limit < 1 or limit > 500:
        raise HTTPException(status_code=400, detail="limit must be between 1 and 500")
    return {"events": recent_events(limit)}


@app.websocket("/ws/events")
async def websocket_events(websocket: WebSocket) -> None:
    await websocket.accept()
    try:
        while True:
            command = await websocket.receive_text()
            if command not in {"latest", "ping"}:
                await websocket.send_json({"error": "unsupported_command"})
                continue
            if command == "ping":
                await websocket.send_json({"type": "pong"})
            else:
                await websocket.send_json({"type": "events", "events": recent_events(50)})
    except WebSocketDisconnect:
        return


@app.get("/metrics", include_in_schema=False)
def metrics() -> Response:
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
