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
