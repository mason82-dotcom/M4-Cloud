from app.config import Settings


def test_fh2_configuration(monkeypatch) -> None:
    monkeypatch.setenv("FH2_UPSTREAM_BASE_URL", "https://fh2.example.local/")
    monkeypatch.setenv("FH2_UPSTREAM_VERIFY_TLS", "false")
    monkeypatch.setenv("DJI_MQTT_TOPICS", "a/#, b/+/c")

    settings = Settings.from_env()

    assert settings.fh2_configured is True
    assert settings.fh2_upstream_base_url == "https://fh2.example.local"
    assert settings.fh2_upstream_verify_tls is False
    assert settings.dji_mqtt_topics == ("a/#", "b/+/c")


def test_cloud_api_subscriptions_are_opt_in(monkeypatch) -> None:
    monkeypatch.setenv("DJI_MQTT_TOPICS", "m4/fh2/#")
    monkeypatch.delenv("DJI_CLOUD_API_ENABLED", raising=False)

    settings = Settings.from_env()

    assert settings.dji_cloud_api_enabled is False
    assert settings.mqtt_subscriptions == ("m4/fh2/#",)


def test_cloud_api_subscriptions_when_enabled(monkeypatch) -> None:
    monkeypatch.setenv("DJI_MQTT_TOPICS", "m4/fh2/#")
    monkeypatch.setenv("DJI_CLOUD_API_ENABLED", "true")

    settings = Settings.from_env()

    assert settings.dji_cloud_api_enabled is True
    assert "thing/product/+/osd" in settings.mqtt_subscriptions
    assert "thing/product/+/events" in settings.mqtt_subscriptions
    assert "sys/product/+/status" in settings.mqtt_subscriptions
