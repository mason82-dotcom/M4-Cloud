import hmac

from fastapi import FastAPI, Header, HTTPException, Query, Response, status
from starlette.concurrency import run_in_threadpool

from app import __version__
from app.adapters.dji_cloud_api import (
    DJICloudAPIAdapter,
    DJICloudAPIError,
    DJICloudAPINotConfigured,
)
from app.adapters.fh2_openapi import FH2Error, FH2NotConfigured, FH2OpenAPIClient
from app.config import get_settings
from app.runtime import database_reachable, mqtt_reachable

app = FastAPI(
    title="M4 Control API",
    version=__version__,
    description="Kanonische API zwischen FH2 OpenAPI V2, DJI Cloud API und M4.",
)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "control-api", "version": __version__}


@app.get("/ready")
async def ready(response: Response) -> dict[str, object]:
    settings = get_settings()
    postgres_ok, mqtt_ok = await run_in_threadpool(
        lambda: (
            database_reachable(settings),
            mqtt_reachable(settings),
        )
    )
    dependencies = {
        "postgres": postgres_ok,
        "mqtt_authenticated": mqtt_ok,
    }
    is_ready = all(dependencies.values())
    if not is_ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return {"ready": is_ready, "dependencies": dependencies}


@app.get("/api/v1/system")
async def system_status() -> dict[str, object]:
    settings = get_settings()
    fh2 = FH2OpenAPIClient(settings)
    cloud = DJICloudAPIAdapter(settings)
    return {
        "service": "m4-cloud",
        "version": __version__,
        "architecture": {
            "fh2_openapi_v2": "separate-adapter",
            "dji_cloud_api": "separate-adapter",
            "lyrebird": "disabled",
        },
        "fh2": {
            "enabled": fh2.enabled,
            "base_configured": fh2.base_configured,
            "organization_configured": fh2.organization_configured,
            "project_configured": fh2.project_configured,
            "verify_tls": settings.fh2_verify_tls,
        },
        "cloud_api": {
            "enabled": cloud.enabled,
            "http_configured": cloud.configured,
            "mqtt_endpoint": cloud.mqtt_endpoint,
            "mqtt_username": cloud.mqtt_username,
            "drc_enabled": False,
        },
    }


@app.get("/api/v1/cloud/bootstrap")
async def cloud_bootstrap(
    x_m4_bootstrap_token: str | None = Header(default=None, alias="X-M4-Bootstrap-Token"),
) -> dict[str, object]:
    settings = get_settings()
    if not settings.dji_bootstrap_token:
        raise HTTPException(status_code=503, detail="bootstrap_not_configured")
    if not x_m4_bootstrap_token or not hmac.compare_digest(
        x_m4_bootstrap_token,
        settings.dji_bootstrap_token,
    ):
        raise HTTPException(status_code=401, detail="invalid_bootstrap_token")
    return DJICloudAPIAdapter(settings).bootstrap_descriptor(include_credentials=True)


@app.get("/api/v1/cameras/status")
async def camera_status() -> dict[str, object]:
    cloud = DJICloudAPIAdapter(get_settings())
    return {
        "enabled": cloud.enabled,
        "configured": cloud.configured,
        "source": "dji-cloud-api-live-capacity",
        "read_only": True,
        "lyrebird": False,
    }


@app.get("/api/v1/cameras/paths")
async def camera_paths() -> dict[str, object]:
    cloud = DJICloudAPIAdapter(get_settings())
    try:
        paths = await cloud.camera_paths()
    except DJICloudAPINotConfigured as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except DJICloudAPIError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return {
        "source": "dji-cloud-api-live-capacity",
        "count": len(paths),
        "paths": [path.model_dump(mode="json") for path in paths],
    }


@app.get("/api/v1/fh2/status")
async def fh2_status() -> dict[str, object]:
    client = FH2OpenAPIClient(get_settings())
    return {
        "enabled": client.enabled,
        "base_configured": client.base_configured,
        "organization_configured": client.organization_configured,
        "project_configured": client.project_configured,
        "read_only": True,
    }


@app.get("/api/v1/fh2/devices")
async def fh2_devices(
    device_class: str = Query(default="drone", pattern="^(drone|airport|base_station)$"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=100, ge=1, le=500),
) -> dict[str, object]:
    client = FH2OpenAPIClient(get_settings())
    try:
        data = await client.list_devices(
            device_model_class=device_class,
            page=page,
            page_size=page_size,
        )
    except FH2NotConfigured as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except FH2Error as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return {"data": data}


@app.get("/api/v1/fh2/flight-tasks")
async def fh2_flight_tasks(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=500),
) -> dict[str, object]:
    client = FH2OpenAPIClient(get_settings())
    try:
        data = await client.list_flight_tasks(page=page, page_size=page_size)
    except FH2NotConfigured as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except FH2Error as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return {"data": data}


@app.get("/api/v1/fh2/waylines")
async def fh2_waylines(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=100, ge=1, le=500),
) -> dict[str, object]:
    client = FH2OpenAPIClient(get_settings())
    try:
        data = await client.list_waylines(page=page, page_size=page_size)
    except FH2NotConfigured as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except FH2Error as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return {"data": data}
