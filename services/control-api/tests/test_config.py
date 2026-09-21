from app.config import Settings


def test_fh2_configuration(monkeypatch) -> None:
    monkeypatch.setenv("FH2_UPSTREAM_BASE_URL", "https://fh2.example.local/")
    monkeypatch.setenv("FH2_USER_TOKEN", "user-token")
    monkeypatch.setenv("FH2_ORG_UUID", "org-123")
    monkeypatch.setenv("FH2_PROJECT_UUID", "project-456")
    monkeypatch.setenv("FH2_LANGUAGE", "en")
    monkeypatch.setenv("FH2_UPSTREAM_VERIFY_TLS", "false")
    monkeypatch.setenv("FH2_TIMEOUT_SECONDS", "7.5")
    monkeypatch.setenv("DJI_MQTT_TOPICS", "a/#, b/+/c")
    monkeypatch.setenv("DJI_CLOUD_API_BASE_URL", "https://cloud.example.local/")
    monkeypatch.setenv("DJI_CLOUD_API_TOKEN", "camera-token")
    monkeypatch.setenv("DJI_CLOUD_API_VERIFY_TLS", "false")
    monkeypatch.setenv("DJI_CLOUD_API_TIMEOUT_SECONDS", "8")

    settings = Settings.from_env()

    assert settings.fh2_configured is True
    assert settings.fh2_upstream_base_url == "https://fh2.example.local"
    assert settings.fh2_user_token == "user-token"
    assert settings.fh2_org_uuid == "org-123"
    assert settings.fh2_project_uuid == "project-456"
    assert settings.fh2_language == "en"
    assert settings.fh2_upstream_verify_tls is False
    assert settings.fh2_timeout_seconds == 7.5
    assert settings.dji_mqtt_topics == ("a/#", "b/+/c")
    assert settings.dji_cloud_api_configured is True
    assert settings.dji_cloud_api_base_url == "https://cloud.example.local"
    assert settings.dji_cloud_api_token == "camera-token"
    assert settings.dji_cloud_api_verify_tls is False
    assert settings.dji_cloud_api_timeout_seconds == 8.0


def test_legacy_fh2_api_token_is_migration_fallback(monkeypatch) -> None:
    monkeypatch.delenv("FH2_USER_TOKEN", raising=False)
    monkeypatch.setenv("FH2_API_TOKEN", "legacy-token")

    settings = Settings.from_env()

    assert settings.fh2_user_token == "legacy-token"
    assert settings.fh2_api_token == "legacy-token"


def test_invalid_fh2_language_falls_back_to_zh(monkeypatch) -> None:
    monkeypatch.setenv("FH2_LANGUAGE", "de")

    settings = Settings.from_env()

    assert settings.fh2_language == "zh"


def test_direct_cloud_ingress_is_opt_in(monkeypatch) -> None:
    monkeypatch.setenv("DJI_MQTT_TOPICS", "m4/fh2/#")
    monkeypatch.delenv("DJI_CLOUD_API_ENABLED", raising=False)
    settings = Settings.from_env()
    assert settings.dji_cloud_api_enabled is False
    assert settings.mqtt_subscriptions == ("m4/fh2/#",)


def test_direct_cloud_ingress_topics_and_worker_credentials(monkeypatch) -> None:
    monkeypatch.setenv("DJI_CLOUD_API_ENABLED", "true")
    monkeypatch.setenv("MQTT_WORKER_USERNAME", "worker-test")
    monkeypatch.setenv("MQTT_WORKER_PASSWORD", "worker-secret")
    settings = Settings.from_env()
    assert settings.mqtt_username == "worker-test"
    assert settings.mqtt_password == "worker-secret"
    assert "thing/product/+/osd" in settings.mqtt_subscriptions
    assert "sys/product/+/status" in settings.mqtt_subscriptions
    assert "thing/product/+/drc/up" not in settings.mqtt_subscriptions
