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


def test_worker_mqtt_credentials(monkeypatch) -> None:
    monkeypatch.setenv("MQTT_WORKER_USERNAME", "worker-test")
    monkeypatch.setenv("MQTT_WORKER_PASSWORD", "secret-test")

    settings = Settings.from_env()

    assert settings.mqtt_username == "worker-test"
    assert settings.mqtt_password == "secret-test"


def test_bootstrap_ready(monkeypatch) -> None:
    values = {
        "DJI_CLOUD_API_ENABLED": "true",
        "DJI_BOOTSTRAP_TOKEN": "bootstrap",
        "DJI_WORKSPACE_ID": "e3dea0f5-37f2-4d79-ae58-490af3228069",
        "DJI_APP_ID": "app-id",
        "DJI_APP_KEY": "app-key",
        "DJI_APP_LICENSE": "license",
        "DJI_API_HOST": "https://m4.example",
        "DJI_API_TOKEN": "api-token",
        "DJI_WS_HOST": "wss://m4.example/ws/dji",
        "DJI_WS_TOKEN": "ws-token",
        "DJI_MQTT_EXTERNAL_HOST": "tcp://m4.example:1883",
        "DJI_MQTT_USERNAME": "dji-pilot",
        "DJI_MQTT_PASSWORD": "mqtt-pass",
    }
    for key, value in values.items():
        monkeypatch.setenv(key, value)

    settings = Settings.from_env()

    assert settings.dji_bootstrap_ready is True
