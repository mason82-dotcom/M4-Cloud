from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    m4_env: str = "development"
    m4_host: str = "0.0.0.0"
    m4_port: int = 8080

    database_url: str = "postgresql://m4:change-me@postgres:5432/m4"

    mqtt_host: str = "mqtt"
    mqtt_port: int = 1883
    mqtt_username: str = "m4-service"
    mqtt_password: str = "change-me-mqtt"

    fh2_enabled: bool = False
    fh2_base_url: str = ""
    fh2_org_id: str = ""
    fh2_project_id: str = ""
    fh2_user_token: str = Field(default="", repr=False)
    fh2_verify_tls: bool = True

    dji_cloud_api_enabled: bool = True


@lru_cache
def get_settings() -> Settings:
    return Settings()
