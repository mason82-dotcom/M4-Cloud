from __future__ import annotations

import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query, Response, WebSocket, WebSocketDisconnect, status
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from .config import APP_NAME, APP_VERSION, Settings
from .db import (
    database_reachable,
    ensure_schema,
    get_worker_heartbeat,
    recent_events,
    store_event,
)
from .fh2 import (
    FH2APIError,
    FH2Client,
    FH2ConfigurationError,
    FH2ConnectionError,
)
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
            "profile": FH2Client.API_PROFILE,
            "organization_configured": bool(settings.fh2_org_uuid),
            "project_configured": bool(settings.fh2_project_uuid),
            "verify_tls": settings.fh2_upstream_verify_tls,
        },
        "integration": {
            "mqtt": {"host": settings.mqtt_host, "port": settings.mqtt_port},
            "https": True,
            "websocket": True,
            "event_persistence": True,
            "metrics": True,
        },
    }


@app.get("/api/v1/fh2/status")
async def fh2_status() -> dict[str, object]:
    settings = Settings.from_env()
    probe = await FH2Client(settings).probe()
    return {
        "configured": settings.fh2_configured,
        "profile": FH2Client.API_PROFILE,
        "organization_configured": bool(settings.fh2_org_uuid),
        "project_configured": bool(settings.fh2_project_uuid),
        "reachable": probe.reachable,
        "authenticated": probe.authenticated,
        "http_status": probe.http_status,
        "business_code": probe.business_code,
        "reason": probe.reason,
    }


@app.get("/api/v1/fh2/devices")
async def fh2_devices(
    device_class: str = Query(default="airport", pattern="^(airport|drone|base_station)$"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=200, ge=1, le=500),
) -> dict[str, object]:
    client = FH2Client(Settings.from_env())
    try:
        data = await client.list_devices(
            device_class=device_class,
            page=page,
            page_size=page_size,
        )
    except FH2ErrorTypes as exc:
        raise _fh2_http_exception(exc) from exc
    return {"data": data}


@app.get("/api/v1/fh2/hms")
async def fh2_hms(
    device_sn: list[str] = Query(min_length=1),
    begin_time_ms: int | None = Query(default=None, ge=0),
    end_time_ms: int | None = Query(default=None, ge=0),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=200),
) -> dict[str, object]:
    now_ms = int(time.time() * 1000)
    end_ms = end_time_ms if end_time_ms is not None else now_ms
    begin_ms = begin_time_ms if begin_time_ms is not None else end_ms - 7 * 24 * 60 * 60 * 1000
    if begin_ms > end_ms:
        raise HTTPException(status_code=400, detail="begin_time_ms must be <= end_time_ms")

    client = FH2Client(Settings.from_env())
    try:
        data = await client.list_hms(
            device_sns=device_sn,
            begin_time_ms=begin_ms,
            end_time_ms=end_ms,
            page=page,
            page_size=page_size,
        )
    except FH2ErrorTypes as exc:
        raise _fh2_http_exception(exc) from exc
    return {"data": data, "window": {"begin_time_ms": begin_ms, "end_time_ms": end_ms}}


@app.get("/api/v1/fh2/waylines")
async def fh2_waylines(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=100, ge=1, le=500),
) -> dict[str, object]:
    client = FH2Client(Settings.from_env())
    try:
        data = await client.list_waylines(page=page, page_size=page_size)
    except FH2ErrorTypes as exc:
        raise _fh2_http_exception(exc) from exc
    return {"data": data}


@app.get("/api/v1/fh2/flight-tasks")
async def fh2_flight_tasks(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=500),
    flight_task_status: int | None = Query(default=None),
    sn: list[str] | None = Query(default=None),
) -> dict[str, object]:
    client = FH2Client(Settings.from_env())
    try:
        data = await client.list_flight_tasks(
            page=page,
            page_size=page_size,
            flight_task_status=flight_task_status,
            sns=sn or (),
        )
    except FH2ErrorTypes as exc:
        raise _fh2_http_exception(exc) from exc
    return {"data": data}


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


FH2ErrorTypes = (FH2ConfigurationError, FH2ConnectionError, FH2APIError)


def _fh2_http_exception(exc: Exception) -> HTTPException:
    if isinstance(exc, FH2ConfigurationError):
        return HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"error": "fh2_not_configured", "reason": str(exc)},
        )
    if isinstance(exc, FH2APIError):
        return HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "error": "fh2_upstream_error",
                "upstream_status": exc.http_status,
                "business_code": exc.business_code,
                "request_id": exc.request_id,
                "reason": str(exc),
            },
        )
    return HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail={"error": "fh2_connection_error", "reason": str(exc)},
    )
