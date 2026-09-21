# Changelog

## Unreleased

### DJI Cloud API Ingress und MQTT-Sicherheit

- geschützter Pilot-2-Bootstrap-Endpunkt
- direkte DJI-MQTT-Uplink-Klassifizierung
- Mosquitto ohne Anonymous Login
- getrennte Rollen für Worker, Health und Pilot
- ACLs für DJI-Uplink/-Downlink; DRC bleibt gesperrt
- lokale Secret-Erzeugung für Quadlet
- Manager-Kommando `dji-cloud-status`
- zentrale CI bleibt ausschließlich `workflow_dispatch` des Direktors


### DJI Kameraerkennung

- Kamera-/Videopfade dynamisch über DJI Cloud API `GET /manage/api/v1/live/capacity`
- Authentifizierung über `x-auth-token`
- Normalisierung von Payload-/Kamera-/Videopfaden zu `video_id`
- Unterstützung für snake_case- und CamelCase-Antwortmodelle
- Manager-Kommandos `camera-status`, `camera-paths` und `camera-telemetry`
- read-only Normalisierung persistierter DJI-MQTT-Kamera-/Gimbal-Telemetrie
- Zuordnung über `device_sn + payload_index`, ohne Modellnamen-Heuristik
- Kamera-, Zoom-, Belichtungs-, Fokus- und optionale Gimbalwinkel
- Lyrebird ist für die Kameraerkennung nicht erforderlich
- Funktion bleibt read-only; keine Stream-/Kamera-/Gimbalsteuerung und kein DRC


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
