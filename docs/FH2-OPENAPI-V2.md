# DJI FlightHub 2 OpenAPI V2 in M4-Cloud

## 1. Ziel

M4-Cloud bindet DJI FlightHub 2 On-Premises / Privatization über die von DJI
veröffentlichte OpenAPI-V2-Schnittstelle an.

Diese erste Integrationsstufe ist bewusst **read-only**. Sie darf weder
Flugaufgaben starten noch Gerätezustände verändern.

Unterstützte Bereiche:

- Geräteübersicht
- HMS-Fehler und Warnungen
- Wayline-/Routenübersicht
- Flugaufgabenübersicht

## 2. Maßgebliche Quellen

Primäre technische Referenz ist das offizielle DJI-Repository:

```text
https://github.com/dji-sdk/FlightHub-2-OpenAPI-V2-Demo
```

Das DJI-Demo dokumentiert getrennte Beispiele für Public Cloud und
Privatization. M4 verwendet in dieser Stufe ausschließlich die im
Privatization-Demo gezeigten V2-Endpunkte.

Als zusätzliche unabhängige Referenz wurde analysiert:

```text
https://pypi.org/project/flighthub2-cli/
https://github.com/alecad/dji-flighthub2-cli
```

`flighthub2-cli` ist **kein DJI-Produkt** und keine Laufzeitabhängigkeit von
M4. M4 kopiert dessen Code nicht. Die Bibliothek dient lediglich als zusätzliche
Plausibilitätsreferenz für typische FlightHub-2-Verhaltensweisen, insbesondere
DJI-Businessfehler und Sicherheitsklassifizierung.

## 3. Authentifizierung

DJI OpenAPI V2 verwendet keinen klassischen Bearer-Token im
`Authorization`-Header.

M4 sendet:

```http
X-User-Token: <Organisation OpenAPI Key>
X-Request-Id: <zufällige UUID>
X-Language: zh
Accept: application/json
User-Agent: M4-Cloud/1.0
```

Bei projektbezogenen Ressourcen zusätzlich:

```http
X-Project-Uuid: <Projekt-/Workspace-UUID>
```

Der Token wird ausschließlich aus der lokalen M4-Konfiguration gelesen und
niemals in Statusantworten ausgegeben.

## 4. Konfiguration

In `.env`:

```env
FH2_UPSTREAM_BASE_URL=https://fh2.example.local
FH2_USER_TOKEN=...
FH2_ORG_UUID=...
FH2_PROJECT_UUID=...
FH2_LANGUAGE=zh
FH2_UPSTREAM_VERIFY_TLS=true
FH2_TIMEOUT_SECONDS=15
```

### FH2_UPSTREAM_BASE_URL

Root-Adresse der On-Premises-/Privatization-Installation.

Richtig:

```text
https://fh2.example.local
http://192.168.178.50:6262
```

Nicht anhängen:

```text
/openapi/v2.0/...
```

Diese Pfade ergänzt M4 selbst.

### FH2_USER_TOKEN

Organisationweiter OpenAPI-Schlüssel. DJI bezeichnet ihn im offiziellen
V2-Demo als Wert für `x-user-token`.

### FH2_ORG_UUID

Organisations-UUID. Sie wird für Geräte und HMS benötigt.

### FH2_PROJECT_UUID

Projekt-/Workspace-UUID. Sie wird für Waylines und Flight Tasks benötigt.

### FH2_LANGUAGE

Aktuell:

```text
zh
en
```

Default ist `zh`, weil das offizielle DJI-Privatization-Demo für HMS
`language=zh` verwendet.

### FH2_UPSTREAM_VERIFY_TLS

Default:

```env
FH2_UPSTREAM_VERIFY_TLS=true
```

Nur bei einer kontrollierten Testinstallation mit selbstsigniertem Zertifikat
vorübergehend auf `false` setzen. Für den Dauerbetrieb ein gültiges oder
lokal vertrauenswürdiges Zertifikat verwenden.

### FH2_TIMEOUT_SECONDS

Timeout pro HTTP-Anfrage. Default:

```env
FH2_TIMEOUT_SECONDS=15
```

## 5. Migration von M4 V1.0

M4 V1.0 verwendete:

```env
FH2_API_TOKEN=
```

Dieser Name war zu allgemein und der damalige Adapter verwendete
`Authorization: Bearer`.

Der V2-Adapter verwendet korrekt:

```env
FH2_USER_TOKEN=
```

Zur Migration akzeptiert M4 `FH2_API_TOKEN` weiterhin als Fallback, wenn
`FH2_USER_TOKEN` leer ist. Neue Installationen sollen ausschließlich
`FH2_USER_TOKEN` verwenden.

## 6. Offizielle Privatization-Endpunkte

### Geräte

DJI:

```http
GET /openapi/v2.0/manage/api/v1/organizations/{orgId}/manage-devices
```

M4:

```http
GET /api/v1/fh2/devices
```

Parameter:

| M4-Parameter | Bedeutung |
| --- | --- |
| `device_class` | `airport`, `drone`, `base_station` |
| `page` | Seite, ab 1 |
| `page_size` | Seitengröße, 1–500 |

Bei `device_class=airport` fragt M4 – entsprechend dem offiziellen DJI-Demo –
beide Klassen ab:

```text
device_model_class=airport
device_model_class=base_station
```

Beispiel:

```bash
curl 'http://127.0.0.1:8080/api/v1/fh2/devices?device_class=drone'
```

Manager:

```bash
./scripts/m4-manager.sh fh2-devices drone
```

### HMS

DJI:

```http
GET /openapi/v2.0/manage/api/v1/organizations/{orgId}/manage-devices/hms
```

M4:

```http
GET /api/v1/fh2/hms
```

Mindestens:

```text
device_sn=<SN>
```

Optional:

```text
begin_time_ms=
end_time_ms=
page=
page_size=
```

Wenn kein Zeitraum gesetzt ist, verwendet M4 die letzten sieben Tage.

Beispiel:

```bash
curl --get \
  --data-urlencode 'device_sn=1581F...' \
  http://127.0.0.1:8080/api/v1/fh2/hms
```

Manager:

```bash
./scripts/m4-manager.sh fh2-hms 1581F...
```

### Waylines

DJI:

```http
GET /openapi/v2.0/wayline/api/v1/workspaces/{projectId}/web-waylines
```

M4:

```http
GET /api/v1/fh2/waylines
```

Beispiel:

```bash
curl 'http://127.0.0.1:8080/api/v1/fh2/waylines?page=1&page_size=100'
```

Manager:

```bash
./scripts/m4-manager.sh fh2-waylines
```

### Flight Tasks

DJI:

```http
GET /openapi/v2.0/task/api/v2/workspaces/{projectId}/flight-tasks
```

M4:

```http
GET /api/v1/fh2/flight-tasks
```

Parameter:

| Parameter | Bedeutung |
| --- | --- |
| `page` | Seite |
| `page_size` | Seitengröße |
| `flight_task_status` | optionaler DJI-Statusfilter |
| `sn` | optional, mehrfach erlaubt |

M4 setzt Seriennummern upstream in DJIs erwartetes Format um:

```text
sn[]=DOCK-A
sn[]=DOCK-B
```

Beispiel:

```bash
curl --get \
  --data-urlencode 'sn=DOCK-A' \
  http://127.0.0.1:8080/api/v1/fh2/flight-tasks
```

Manager:

```bash
./scripts/m4-manager.sh fh2-tasks DOCK-A
```

## 7. Statusprüfung

```bash
./scripts/m4-manager.sh fh2-status
```

Mögliche Antwort:

```json
{
  "configured": true,
  "profile": "privatization-openapi-v2",
  "organization_configured": true,
  "project_configured": true,
  "reachable": true,
  "authenticated": true,
  "http_status": 200,
  "business_code": null,
  "reason": "openapi_ok"
}
```

Für die Probe verwendet M4 keinen erfundenen Health-Endpunkt. Sobald
Organisation, URL und Token vorhanden sind, wird ein minimaler, read-only
Geräteaufruf gegen den offiziellen V2-Pfad verwendet.

## 8. Fehlersemantik

### Lokale Konfiguration fehlt

M4 antwortet:

```text
HTTP 503
```

Beispiel:

```json
{
  "detail": {
    "error": "fh2_not_configured",
    "reason": "FH2_PROJECT_UUID is not configured"
  }
}
```

### FH2 nicht erreichbar

M4 antwortet:

```text
HTTP 502
```

mit:

```text
fh2_connection_error
```

### DJI HTTP- oder Businessfehler

FlightHub 2 kann fachliche Fehler mit HTTP 200, aber einem nicht-null bzw.
nicht-zero Feld `code` zurückgeben.

M4 behandelt:

```json
{
  "code": 230001,
  "message": "..."
}
```

nicht als Erfolg.

Stattdessen liefert M4 an seinen Client:

```text
HTTP 502
fh2_upstream_error
```

mit Upstream-HTTP-Status, Business-Code und der von M4 erzeugten Request-ID.

## 9. Sicherheitsgrenze

Phase A ist hart auf **GET/read-only** begrenzt.

Nicht implementiert:

- Flight Task erstellen
- Flight Task starten
- Flight Task stoppen
- RTH
- Aircraft Control
- Payload Control
- Wayline Upload
- Annotation schreiben/löschen
- Rekonstruktion starten/löschen
- andere physische oder destruktive Aktionen

Solche Funktionen werden später getrennt klassifiziert:

```text
READ
WRITE
DANGEROUS
```

`DANGEROUS` darf niemals implizit durch einen allgemeinen API-/Agentenzugriff
freigeschaltet werden.

## 10. Manager-Kommandos

```bash
./scripts/m4-manager.sh fh2-status
./scripts/m4-manager.sh fh2-devices airport
./scripts/m4-manager.sh fh2-devices drone
./scripts/m4-manager.sh fh2-hms <DEVICE_SN>
./scripts/m4-manager.sh fh2-waylines
./scripts/m4-manager.sh fh2-tasks
./scripts/m4-manager.sh fh2-tasks <DEVICE_SN>
```

Vollständiger Live-Read-Test gegen den konfigurierten FH2-Upstream:

```bash
./scripts/m4-manager.sh fh2-verify
```

`fh2-verify` benötigt echte FH2-Zugangsdaten und ist daher bewusst nicht Teil
des normalen lokalen `verify`.

## 11. Normaler M4-Verifikationstest

```bash
./scripts/m4-manager.sh verify
```

Dieser Test bleibt unabhängig von DJI-Zugangsdaten.

Zusätzlich zu Health/Readiness, PostgreSQL und MQTT prüft er, dass das laufende
M4-Control-API-Image folgende FH2-Routen tatsächlich im OpenAPI-Schema enthält:

```text
/api/v1/fh2/devices
/api/v1/fh2/hms
/api/v1/fh2/waylines
/api/v1/fh2/flight-tasks
```

## 12. Entwicklung und Tests

Die FH2-Tests verwenden keinen echten DJI-Server.

`httpx.MockTransport` prüft unter anderem:

- offizielle V2-Pfade
- `X-User-Token`
- `X-Project-Uuid`
- `X-Request-Id`
- kein `Authorization: Bearer`
- wiederholte `device_model_class`-Parameter
- `sn[]` für Taskfilter
- Businessfehler bei `code != 0`
- fehlende Projektkonfiguration

Tests:

```bash
cd services/control-api
PYTHONPATH=. pytest -q
```

## 13. Nächste Stufe

Nach erfolgreicher Verifikation gegen deine reale FH2-On-Premises-Installation:

1. Antwortmodelle der tatsächlich eingesetzten FH2-Version erfassen.
2. Geräte-/HMS-Daten optional lokal cachen.
3. Media-Endpunkte ergänzen.
4. Livestream-Metadaten ergänzen.
5. Write-Operationen separat implementieren.
6. Dangerous-Operationen mit explizitem Policy-/Freigabemechanismus absichern.

Die Read-only-Schicht bleibt dabei die sichere Grundlage.
