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
- **Docker Compose**: ohne Architektur-Pinning, dadurch für x86_64 und ARM64/Raspberry Pi geeignet.

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

## Raspberry Pi / ARM64

V2.0 setzt keine feste Container-Plattform. Die verwendeten Basisimages sind
für den normalen Docker-Compose-Betrieb auf ARM64 geeignet. Auf einem
Raspberry Pi 5 kann derselbe Startpfad verwendet werden:

```bash
cp .env.example .env
docker compose up -d --build
./scripts/verify.sh
```

## Projektregeln

- Arbeits- und Lieferbranch: `main`
- nur der **Direktor** startet und bewertet CI
- Manager, RC Pro und Multispektral starten keine CI
- keine M3-Cloud-Abhängigkeit
- keine Lyrebird-Abhängigkeit
- keine Secrets im Repository
- keine DRC-/Flugsteuerung in V2.0
