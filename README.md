# M4-Cloud V2.0

M4-Cloud ist die lokale Integrationsplattform zwischen DJI FlightHub 2,
DJI OpenAPI V2, DJI Cloud API und den M4-Anwendungen.

## Status

Aktueller Produktstand: **2.0.0 auf `main`**.

Die V2.0-Basis ist bewusst kompakt und funktional:

- **FH2 OpenAPI V2**: read-only Adapter für Geräte, Waylines und Flight Tasks.
- **DJI Cloud API**: separater HTTP-/MQTT-Integrationspfad.
- **Kameraerkennung**: dynamisch über `/manage/api/v1/live/capacity`.
- **Control API**: einheitliche interne REST-API.
- **PostgreSQL**: Laufzeitabhängigkeit mit echter Readiness-Prüfung.
- **Mosquitto**: authentifiziert, getrennte Rollen für M4 und DJI/RC.
- **MQTT ACL**: DJI-Basic-Link-Pfade freigegeben, DRC explizit nicht freigegeben.
- **Lyrebird**: deaktiviert.
- **Docker Compose**: ohne unnötiges Plattform-Pinning für den vorgesehenen Docker-Host.

## Architektur

```text
FlightHub 2 ── OpenAPI V2 ──┐
                            ├── M4 Control API
RC Pro / Aircraft ─ Cloud API┘         │
             │                         ├── PostgreSQL
             └──────── MQTT ───────────└── Mosquitto
```

FH2 OpenAPI V2 und DJI Cloud API bleiben getrennte Adapter.

## Installation

```bash
git switch main
git pull --ff-only
cp .env.example .env
```

Danach mindestens ändern:

```env
POSTGRES_PASSWORD=<sicheres-passwort>

MQTT_SERVICE_PASSWORD=<sicheres-m4-mqtt-passwort>
DJI_MQTT_PASSWORD=<sicheres-dji-mqtt-passwort>

# IP/Hostname des M4-Hosts, den die RC Pro erreichen kann
MQTT_PUBLIC_HOST=192.168.x.x
```

Optional FH2 konfigurieren:

```env
FH2_ENABLED=true
FH2_BASE_URL=https://...
FH2_ORG_ID=...
FH2_PROJECT_ID=...
FH2_USER_TOKEN=...
```

Optional DJI Cloud API HTTP-Kameraerkennung:

```env
DJI_CLOUD_API_BASE_URL=https://...
DJI_CLOUD_API_ACCESS_TOKEN=...
```

## Start

```bash
docker compose up -d --build
```

Prüfen:

```bash
curl http://127.0.0.1:8080/health
curl http://127.0.0.1:8080/ready
curl http://127.0.0.1:8080/api/v1/system
```

Komplette lokale V2-Basisprüfung:

```bash
./scripts/verify.sh
```

Der Verify-Pfad baut und startet den Stack, prüft Readiness/API und testet
beide MQTT-Rollen. Der Stack bleibt danach gestartet.

## API

System:

```text
GET /health
GET /ready
GET /api/v1/system
```

DJI Cloud API / RC:

```text
GET /api/v1/cloud/bootstrap
GET /api/v1/cameras/status
GET /api/v1/cameras/paths
```

FH2 OpenAPI V2:

```text
GET /api/v1/fh2/status
GET /api/v1/fh2/devices
GET /api/v1/fh2/waylines
GET /api/v1/fh2/flight-tasks
```

## MQTT-Rollen

### M4-Service

Der interne Benutzer darf:

- `m4/#` lesen/schreiben
- DJI Status/State/OSD/Requests/Events/Replies lesen
- DJI `services` und `property/set` schreiben

### DJI-/RC-Client

Der externe DJI-/RC-Benutzer darf:

- Status/State/OSD/Requests/Events/Replies publizieren
- `services` und `property/set` abonnieren

Nicht freigegeben:

```text
thing/product/+/drc/up
thing/product/+/drc/down
```

MQTT läuft in V2.0 ohne TLS und ist daher für das vertrauenswürdige Heim-/LAN-Netz vorgesehen. Für WAN-Zugriff muss TLS bzw. ein gesicherter Tunnel vorgeschaltet werden.

## Zielhost

V2.0 ist für den vorhandenen Docker-/WSL-Host vorgesehen.

## Projektregeln

- Arbeits- und Lieferbranch: `main`
- nur der **Direktor** startet und bewertet CI
- Manager, RC Pro und Multispektral starten keine CI
- keine M3-Cloud-Abhängigkeit
- keine Lyrebird-Abhängigkeit
- keine Secrets im Repository
- keine DRC-/Flugsteuerung in V2.0


## Entwicklungscontainer

Für VS Code steht eine schlanke Python-3.12-Dev-Container-Konfiguration unter
`.devcontainer/` bereit. Die M4-Runtime-Dienste bleiben außerhalb des
Entwicklungscontainers.

Siehe `docs/DEVCONTAINER.md`.


## Echtzeit-Telemetrie

Die WebUI kann DJI OSD-/State-/Event-/Statusdaten read-only über
`/ws/v1/telemetry` empfangen. Status: `GET /api/v1/telemetry/status`.

Siehe `docs/TELEMETRY-WEBSOCKET.md`.


## DRC

DRC bleibt deaktiviert. Die verifizierte Topic-/Sequenzsemantik und die
Sicherheits-Gates sind in `docs/DRC-DESIGN.md` dokumentiert.


## RC Pro Discovery

Gateway↔Aircraft-Zuordnung über DJI `update_topo` ist in
`docs/RC-PRO-DISCOVERY.md` beschrieben. M4 entfernt dabei
`device_secret` und `nonce` vor jeder WebUI-Ausgabe.
