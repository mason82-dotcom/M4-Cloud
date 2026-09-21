# Direktor-Handoff: DJI Cloud API / MQTT

## Zweck

Dieser Stand arbeitet dem Direktor zu. Er startet **keine** CI und verändert
keine CI-Trigger. Der vorhandene Workflow bleibt ausschließlich
`workflow_dispatch`.

Kandidatenbranch:

```text
agent/director-support
```

## Aktueller kanonischer Stand

Der aktuelle M4-Neuaufbau trennt:

- FlightHub 2 OpenAPI V2 als ausgehenden read-only Adapter
- DJI Cloud API als separaten MQTT-/HTTP-/WebSocket-Pfad
- ein gemeinsames M4-Domainmodell
- Lyrebird deaktiviert
- DRC deaktiviert

## Bereits vorhanden

### MQTT

- `allow_anonymous false`
- Password-Datei wird beim Compose-Start erzeugt
- ACL-Datei wird beim Compose-Start erzeugt
- separater M4-Service-Benutzer
- separater DJI-Benutzer
- DRC-Topics nicht freigegeben
- Readiness prüft MQTT mit Service-Credentials

### DJI Cloud API

- Bootstrap-Descriptor ohne MQTT-Passwort
- dokumentierte Publish-/Subscribe-Topics
- read-only Kamera-Capacity über
  `GET /manage/api/v1/live/capacity`
- DRC deaktiviert

### FH2 OpenAPI V2

- separater Adapter
- `X-User-Token`
- `X-Project-Uuid`
- `X-Request-Id`
- read-only Geräte, Waylines und Flight Tasks

## Änderung dieses Kandidaten

Die Defaults werden bewusst sicher:

```env
MQTT_BIND=127.0.0.1
MQTT_PUBLIC_HOST=127.0.0.1
DJI_CLOUD_API_ENABLED=false
```

Damit wird MQTT nicht versehentlich ohne TLS im LAN veröffentlicht und die
direkte Cloud-API-Anbindung muss explizit aktiviert werden.

## Lokale Manager-Prüfung vor Director-CI

Diese Prüfungen dürfen Manager/Fachagenten lokal ausführen:

```bash
cd services/control-api
python -m compileall -q app
python -m pytest -q tests
ruff check app tests

cd ../..
docker compose config
```

Für einen bewusst lokalen Runtime-Test:

```bash
docker compose up -d --build
curl -fsS http://127.0.0.1:8080/health
curl -fsS http://127.0.0.1:8080/ready
curl -fsS http://127.0.0.1:8080/api/v1/system
curl -fsS http://127.0.0.1:8080/api/v1/cloud/bootstrap
```

Zusätzlich prüfen:

1. MQTT ohne Benutzer/Passwort wird abgewiesen.
2. `m4-service` kann sich authentifizieren.
3. `dji-client` kann nur die freigegebenen DJI-Topics verwenden.
4. DRC-Topics sind nicht erlaubt.
5. Bootstrap liefert kein MQTT-Passwort.

## Offene Punkte vor echter RC-Pro-/Pilot-2-Freigabe

Nicht als fertig markieren:

- separater MQTT-TLS-Listener
- Zertifikat-/Trust-Chain-Test mit realer Pilot-2-Version
- Pilot-2-H5-/JSBridge-Login und License Verify
- sichere Credential-Ausgabe/Session für Pilot 2
- WebSocket-Authentifizierung
- dynamische Device-/RC-spezifische ACLs
- Gerätekommandos
- DRC

## Director-CI

Nur der Direktor entscheidet, wann der manuelle Workflow gestartet wird.

Vor Merge nach `main` sollte der Direktor mindestens bewerten:

- Ruff
- Pytest
- Compose-Konfiguration
- keine Secret-Ausgabe
- MQTT-Auth/ACL
- FH2-Adapter-Regressionsfreiheit
- DJI-Cloud-Adapter-Regressionsfreiheit

Der Manager startet diesen Workflow nicht.
