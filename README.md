# M4-Cloud

Eigenständiger Integrations- und Kontrollserver für **DJI FlightHub 2 On-Premises**.

> M4-Cloud ist vollständig unabhängig von M3-Cloud. Proprietäre DJI-FlightHub-2-Komponenten werden nicht nachgebaut, kopiert oder redistribuiert. Das offiziell bereitgestellte/lizenzierte FH2-On-Premises-System bzw. DJI FH2 AIO bleibt der DJI-Upstream.

## V1.1.0

M4-Cloud V1.1 stellt die vollständige eigene Integrations- und Betriebsschicht bereit:

- Docker-Compose-Deployment
- Nginx Reverse Proxy
- FastAPI Control API
- PostgreSQL-Persistenz
- MQTT-Broker
- MQTT-Integration-Worker
- HTTPS/FH2-Upstream-Adapter
- WebSocket-Ereigniskanal
- neutraler HTTP-Webhook-Eingang
- Prometheus-Metriken und optionaler Prometheus-Dienst
- Health-/Readiness-Prüfungen
- Backup-/Restore-Runbook
- CI-End-to-End-Abnahme

## Arbeitsmodell

Neue M4-Features werden vom **Manager** geliefert und direkt in `main`
integriert. **RC Pro** unterstützt bei DJI-Controller-, Mobile-SDK- und
Geräteintegration; **Multispektral** unterstützt bei Kamera-, Medien-,
Mapping- und multispektralen Datenpfaden.

Der Manager führt beide Fachbeiträge zusammen, hält Backend, Deployment,
Tests und Dokumentation konsistent und ist die zentrale Integrationsstelle.

Ausführlich: `docs/PROJECT-WORKFLOW.md`.

## Schnellstart

```bash
cp .env.example .env
# POSTGRES_PASSWORD in .env ändern
docker compose up -d --build

curl http://localhost:8080/health
curl http://localhost:8080/ready
curl http://localhost:8080/api/v1/system/status
curl http://localhost:8080/api/v1/fh2/status
```

Vollständige lokale Abnahme unter Linux/WSL2:

```bash
sh scripts/verify.sh
```

Unter Windows PowerShell:

```powershell
.\scripts\verify.ps1
```

Für WSL2 + Ubuntu + das neue Microsoft-WSLC siehe `docs/SETUP-WSL2-WSLC.md`.

## Dienste

| Dienst | Aufgabe | Host-Port |
| --- | --- | --- |
| `reverse-proxy` | HTTP/API/WebSocket-Einstieg | 8080 |
| `control-api` | M4-Control- und Integrations-API | intern |
| `integration-worker` | MQTT-Ereignisse -> PostgreSQL | intern |
| `postgres` | M4-eigene Persistenz | intern |
| `mqtt` | MQTT-Integrationspunkt | 127.0.0.1:1883 |
| `prometheus` | optionales Monitoring-Profil | 127.0.0.1:9090 |

## DJI FlightHub 2 anbinden

In `.env`:

```env
FH2_UPSTREAM_BASE_URL=https://fh2.example.local
FH2_USER_TOKEN=...
FH2_ORG_UUID=...
FH2_PROJECT_UUID=...
FH2_LANGUAGE=zh
FH2_UPSTREAM_VERIFY_TLS=true
```

M4 enthält jetzt eine read-only DJI FlightHub 2 Privatization OpenAPI-V2-
Integration auf Basis des offiziellen DJI-Demos. Unterstützt sind Geräte, HMS,
Waylines und Flight Tasks. Schreibende oder flugwirksame Funktionen sind in
dieser Stufe absichtlich nicht freigeschaltet.

Komfortabel über den Manager:

```bash
./scripts/m4-manager.sh fh2-status
./scripts/m4-manager.sh fh2-devices drone
./scripts/m4-manager.sh fh2-waylines
./scripts/m4-manager.sh fh2-tasks
```

Ausführliche deutsche Dokumentation: `docs/FH2-OPENAPI-V2.md`.

Dynamische Kamera-/Videopfad-Erkennung aus der DJI Cloud API:

```bash
./scripts/m4-manager.sh camera-status
./scripts/m4-manager.sh camera-paths
./scripts/m4-manager.sh camera-telemetry
```

M4 liest dafür read-only `/manage/api/v1/live/capacity` ein und normalisiert
die gemeldeten `video_id`-/Payload-Pfade. Zusätzlich kann
`camera-telemetry` bereits persistierte DJI-MQTT-Kamera- und Gimbalwerte pro
`device_sn + payload_index` zusammenführen. Lyrebird wird dafür nicht
benötigt. Details: `docs/CAMERA-PATHS.md`.

Für MQTT werden die offiziell für die Zielinstallation vorgesehenen Topics
über `DJI_MQTT_TOPICS` gesetzt.

## Dokumentation

- `docs/ARCHITECTURE.md` – Systemgrenzen und Komponenten
- `docs/DJI-INTEGRATION.md` – DJI/FH2-Anbindung
- `docs/FH2-OPENAPI-V2.md` – FH2 Privatization OpenAPI V2, Auth, Endpunkte und Manager
- `docs/CAMERA-PATHS.md` – dynamische DJI Kamera-/Videopfad-Erkennung
- `docs/API.md` – Control API
- `docs/NETWORK.md` – Ports und Netzwerk
- `docs/OPERATIONS.md` – Betrieb, Monitoring, Backup und Restore
- `docs/SETUP-WSL2-WSLC.md` – Windows 11, WSL2, Ubuntu, VS Code und WSLC
- `docs/SETUP-PODMAN-QUADLET.md` – Docker-Desktop-freier Betrieb mit Podman und Quadlet
- `SECURITY.md` – Sicherheitsvorgaben
