from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    m4_env: str = "development"
    m4_host: str = "0.0.0.0"
    m4_port: int = 8080

    database_url: str = Field(
        default="postgresql://m4:change-me@postgres:5432/m4",
        repr=False,
    )

    mqtt_host: str = "mqtt"
    mqtt_port: int = 1883
    mqtt_public_host: str = "127.0.0.1"
    mqtt_public_port: int = 1883
    mqtt_service_username: str = "m4-service"
    mqtt_service_password: str = Field(default="change-me-mqtt", repr=False)
    dji_mqtt_username: str = "dji-client"
    dji_mqtt_password: str = Field(default="change-me-dji-mqtt", repr=False)
    dji_bootstrap_token: str = Field(default="", repr=False)

    fh2_enabled: bool = False
    fh2_base_url: str = ""
    fh2_org_id: str = ""
    fh2_project_id: str = ""
    fh2_user_token: str = Field(default="", repr=False)
    fh2_verify_tls: bool = True
    fh2_timeout_seconds: float = 15.0

    dji_cloud_api_enabled: bool = True
    dji_cloud_api_base_url: str = ""
    dji_cloud_api_access_token: str = Field(default="", repr=False)
    dji_cloud_api_verify_tls: bool = True
    dji_cloud_api_timeout_seconds: float = 15.0


@lru_cache
def get_settings() -> Settings:
    return Settings()
