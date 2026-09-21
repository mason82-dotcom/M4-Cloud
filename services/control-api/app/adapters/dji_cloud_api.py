from dataclasses import dataclass

from app.config import Settings


@dataclass(frozen=True)
class DJICloudAPIAdapter:
    """Konfigurationsgrenze für den DJI-Cloud-API-Pfad.

    MQTT/HTTPS/WebSocket werden hier bewusst getrennt von FH2 OpenAPI V2 gehalten.
    """

    settings: Settings

    @property
    def enabled(self) -> bool:
        return self.settings.dji_cloud_api_enabled

    @property
    def mqtt_endpoint(self) -> str:
        return f"{self.settings.mqtt_host}:{self.settings.mqtt_port}"
