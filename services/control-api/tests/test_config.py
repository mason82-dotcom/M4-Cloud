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
