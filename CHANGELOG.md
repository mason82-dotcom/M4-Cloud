# Changelog

## Unreleased

### DJI Kameraerkennung

- Kamera-/Videopfade dynamisch über DJI Cloud API `GET /manage/api/v1/live/capacity`
- Authentifizierung über `x-auth-token`
- Normalisierung von Payload-/Kamera-/Videopfaden zu `video_id`
- Unterstützung für snake_case- und CamelCase-Antwortmodelle
- Manager-Kommandos `camera-status` und `camera-paths`
- Lyrebird ist für die Kameraerkennung nicht erforderlich
- Funktion bleibt read-only; keine Stream-/Kamerasteuerung


## 1.1.0

### Deployment und Entwicklung

- rootless Podman/Quadlet-Deployment
- zentraler `scripts/m4-manager.sh`
- systemd-User-Services und M4-Target
- Podman-/Quadlet-Dokumentation und VS-Code-Grundintegration

### DJI FlightHub 2

- Privatization OpenAPI V2 Read-only-Adapter
- korrekte Authentifizierung über `X-User-Token`
- `X-Project-Uuid`, `X-Request-Id` und `X-Language`
- Geräte- und HMS-Abfragen
- Wayline- und Flight-Task-Abfragen
- DJI-Businessfehler `code != 0` werden als Fehler behandelt
- Manager-Kommandos für FH2
- ausführliche deutsche FH2-V2-Dokumentation

### Sicherheit

- keine Write-/Dangerous-FH2-Operationen in dieser Stufe
- keine Secrets oder Upstream-URL im M4-Status
- `FH2_API_TOKEN` nur noch als Migrations-Fallback; neu: `FH2_USER_TOKEN`

## 1.0.0

- erster validierter M4-Cloud Kontroll- und Integrationsstack
- Nginx Reverse Proxy
- FastAPI Control API
- PostgreSQL
- MQTT Broker und Integration Worker
- HTTP-/WebSocket-Ereignisschnittstellen
- Prometheus
- Health-/Readiness-Prüfungen
- Docker-Compose-End-to-End-CI
