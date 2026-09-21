from enum import StrEnum

from pydantic import BaseModel, Field


class IntegrationSource(StrEnum):
    FH2_OPENAPI_V2 = "fh2_openapi_v2"
    DJI_CLOUD_API = "dji_cloud_api"
    MSDK_V5 = "msdk_v5"


class CameraCapability(BaseModel):
    photo: bool = False
    video: bool = False
    zoom: bool = False
    thermal: bool = False
    multispectral: bool = False


class CameraState(BaseModel):
    source: IntegrationSource
    payload_index: int = 0
    lens_index: int | None = None
    mode: str | None = None
    live_source: str | None = None
    zoom_factor: float | None = None
    focal_length_mm: float | None = None
    iso: int | None = None
    shutter_speed: str | None = None
    aperture: float | None = None
    capabilities: CameraCapability = Field(default_factory=CameraCapability)


class GimbalState(BaseModel):
    source: IntegrationSource
    payload_index: int = 0
    pitch_deg: float | None = None
    roll_deg: float | None = None
    yaw_deg: float | None = None
    mode: str | None = None
