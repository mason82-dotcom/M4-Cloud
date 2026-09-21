from fastapi import FastAPI

from app import __version__
from app.adapters.dji_cloud_api import DJICloudAPIAdapter
from app.adapters.fh2_openapi import FH2OpenAPIClient
from app.config import get_settings

app = FastAPI(
    title="M4 Control API",
    version=__version__,
    description="Kanonische API zwischen FH2 OpenAPI V2, DJI Cloud API und M4.",
)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "control-api", "version": __version__}


@app.get("/ready")
async def ready() -> dict[str, object]:
    settings = get_settings()
    cloud = DJICloudAPIAdapter(settings)
    return {
        "ready": True,
        "dependencies": {
            "fh2_required": False,
            "fh2_configured": FH2OpenAPIClient(settings).configured,
            "dji_cloud_api_enabled": cloud.enabled,
            "mqtt_endpoint": cloud.mqtt_endpoint,
        },
    }


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
            "enabled": settings.fh2_enabled,
            "configured": fh2.configured,
            "verify_tls": settings.fh2_verify_tls,
        },
        "cloud_api": {
            "enabled": cloud.enabled,
            "mqtt_endpoint": cloud.mqtt_endpoint,
        },
    }
