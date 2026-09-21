from app.config import Settings


def test_secure_defaults_require_explicit_dji_external_enablement() -> None:
    settings = Settings(_env_file=None)

    assert settings.dji_cloud_api_enabled is False
    assert settings.mqtt_public_host == "127.0.0.1"
    assert settings.mqtt_public_port == 1883
