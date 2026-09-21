# M4-Cloud

M4-Cloud ist der eigene Integrations-, Persistenz- und Kontroll-Layer für zwei getrennte DJI-Pfade:

- **DJI FlightHub 2 Privatization OpenAPI V2**: M4 -> vorhandener FH2-On-Premises-Server
- **DJI Cloud API**: DJI Pilot 2 / Dock -> M4

M4 bildet keine proprietären DJI-Komponenten nach und bleibt unabhängig von M3-Cloud und Lyrebird.

## Version 1.1.0

Aktuell vorhanden:

- rootless Podman + Quadlet für WSL2/Linux
- Docker Compose als Referenz-/Director-Validation-Pfad
- Nginx Reverse Proxy
- FastAPI Control API
- PostgreSQL
- gehärteter Mosquitto-Broker mit Benutzer-/Passwortauthentifizierung und ACLs
- MQTT Integration Worker
- DJI Cloud API MQTT-Ingest
- Pilot-2-Bootstrap-API
- dynamische Kamera-/Videopfad-Erkennung über `/manage/api/v1/live/capacity`
- normalisierte Kamera-/Gimbal-Telemetrie aus MQTT-Events
- FH2 Privatization OpenAPI V2 read-only für Geräte, HMS, Waylines und Flight Tasks
- Prometheus-Metriken
- Health-/Readiness- und Persistenzabnahme

## Sicherheitsgrenzen

Noch nicht freigegeben:

- kein externer MQTT-TLS-Listener
- keine fertige Pilot-2-H5-/JSBridge-Einstiegsseite
- keine DJI-Gerätekommandos
- kein DRC
- keine ungeschützte Internetfreigabe

MQTT bleibt am Host standardmäßig auf `127.0.0.1:1883`.

## Empfohlener lokaler Betrieb

Unter Ubuntu/WSL2:

```bash
cd ~/src/M4-Cloud
cp -n .env.example .env
chmod 600 .env
nano .env
# POSTGRES_PASSWORD setzen

./scripts/m4-manager.sh install
./scripts/m4-manager.sh start
./scripts/m4-manager.sh verify
```

Der Installer erzeugt fehlende interne Secrets lokal und baut Control API sowie den gehärteten MQTT-Broker.

## Manager

```bash
./scripts/m4-manager.sh status
./scripts/m4-manager.sh dji-cloud-status
./scripts/m4-manager.sh camera-status
./scripts/m4-manager.sh camera-paths
./scripts/m4-manager.sh camera-telemetry

./scripts/m4-manager.sh fh2-status
./scripts/m4-manager.sh fh2-devices drone
./scripts/m4-manager.sh fh2-waylines
./scripts/m4-manager.sh fh2-tasks
```

## DJI Cloud API

Direkter Ingress wird über `DJI_CLOUD_API_ENABLED=true` aktiviert.

Status:

```text
GET /api/v1/dji/cloud/status
```

M4-Bootstrap für die spätere Pilot-2-H5-Seite:

```text
GET /api/v1/dji/cloud/bootstrap
X-M4-Bootstrap-Token: <DJI_BOOTSTRAP_TOKEN>
```

Die Bootstrap-Antwort enthält sensible Laufzeitwerte und darf bei realer Pilot-2-Anbindung erst über HTTPS verwendet werden.

## FH2 OpenAPI V2

Konfiguration:

```env
FH2_UPSTREAM_BASE_URL=https://fh2.example.local
FH2_USER_TOKEN=...
FH2_ORG_UUID=...
FH2_PROJECT_UUID=...
FH2_LANGUAGE=zh
FH2_UPSTREAM_VERIFY_TLS=true
```

Die Integration ist read-only. Details: `docs/FH2-OPENAPI-V2.md`.

## Arbeitsmodell

- **Manager**: Features, lokale Tests, Doku, Integration
- **RC Pro**: DJI-Controller-/Gerätepfad
- **Multispektral**: Kamera-/Medien-/Mapping-Pfad
- **Direktor**: alleiniger Owner der CI

GitHub Actions bleibt deshalb auf `workflow_dispatch`; Manager, RC Pro und Multispektral starten keine CI-Läufe.

## Dokumentation

- `docs/ARCHITECTURE.md`
- `docs/DJI-INTEGRATION.md`
- `docs/FH2-OPENAPI-V2.md`
- `docs/CAMERA-PATHS.md`
- `docs/API.md`
- `docs/NETWORK.md`
- `docs/OPERATIONS.md`
- `docs/SETUP-PODMAN-QUADLET.md`
- `docs/SETUP-WSL2-WSLC.md`
- `docs/PROJECT-WORKFLOW.md`
- `SECURITY.md`
