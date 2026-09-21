# DJI FlightHub 2 Integration

## Zweck

M4-Cloud ergänzt eine offiziell bereitgestellte DJI FlightHub 2
On-Premises-/Privatization-Installation. Das Repository enthält keine
proprietären FlightHub-2-Serverbinärdateien und bildet keine DJI-internen
Dienste nach.

## FH2 OpenAPI V2

Die erste produktive FH2-HTTP-Integration orientiert sich an DJIs offiziellem
Repository `dji-sdk/FlightHub-2-OpenAPI-V2-Demo`.

Konfiguration:

```env
FH2_UPSTREAM_BASE_URL=https://fh2.example.local
FH2_USER_TOKEN=...
FH2_ORG_UUID=...
FH2_PROJECT_UUID=...
FH2_LANGUAGE=zh
FH2_UPSTREAM_VERIFY_TLS=true
FH2_TIMEOUT_SECONDS=15
```

Authentifizierung:

- `X-User-Token`
- `X-Request-Id`
- `X-Language`
- projektbezogen zusätzlich `X-Project-Uuid`

Der frühere M4-V1.0-Name `FH2_API_TOKEN` wird nur noch als
Migrations-Fallback gelesen. Neue Installationen verwenden
`FH2_USER_TOKEN`.

## Read-only Ressourcen

M4 implementiert derzeit ausschließlich dokumentierte GET-Operationen:

- Geräte
- HMS
- Waylines
- Flight Tasks

M4-Control-API:

```text
GET /api/v1/fh2/status
GET /api/v1/fh2/devices
GET /api/v1/fh2/hms
GET /api/v1/fh2/waylines
GET /api/v1/fh2/flight-tasks
```

Ausführlich: `docs/FH2-OPENAPI-V2.md`.

## Fehlerbehandlung

DJI kann fachliche Fehler mit HTTP 200 und `code != 0` zurückgeben. M4
behandelt solche Antworten als Upstream-Fehler und nicht als Erfolg.

Secrets und die konkrete FH2-Upstream-URL werden nicht in Statusantworten
ausgegeben.

## Sicherheitsgrenze

In dieser Phase existieren keine M4-Endpunkte zum:

- Starten oder Erstellen von Flugaufgaben
- Steuern von Luftfahrzeugen
- RTH
- Payload Control
- Löschen von DJI-Daten
- Starten kosten-/quota-relevanter Rekonstruktionen

Spätere Operationen werden in `READ`, `WRITE` und `DANGEROUS` getrennt.

## MQTT

Der Worker abonniert die in `DJI_MQTT_TOPICS` konfigurierten Topics und
persistiert empfangene Ereignisse. Standard bleibt `m4/fh2/#`; reale
DJI-Topics werden erst gemäß der eingesetzten FH2-/Cloud-API-Konfiguration
eingetragen.

## Kamera-/Gimbal-Telemetrie

Persistierte DJI-MQTT-Ereignisse aus `thing/product/<sn>/osd` und
`thing/product/<sn>/state` können read-only zu einem aktuellen
Payload-Snapshot normalisiert werden:

```text
GET /api/v1/cameras/telemetry
```

Die stabile Zuordnung erfolgt über `device_sn + payload_index`. Kamera-State
und optionale Gimbalwinkel werden nur übernommen, wenn sie im empfangenen
DJI-Payload vorhanden sind. Fehlende Payload-Zuordnungen werden nicht anhand
des Gerätemodells geraten.

Der Parser kann bereits persistierte DRC-Telemetrie lesen, aktiviert aber
weder DRC noch Kamera-, Gimbal- oder Payload-Steuerung.

Details: `docs/CAMERA-PATHS.md`.

## HTTP-Events

`POST /api/v1/events` ist ein neutraler M4-Webhook-Eingang für offiziell
konfigurierte FH2-/Sync-Ereignisse oder eigene Adapter.

## WebSocket

`/ws/events` ist ein M4-eigener Live-Kanal mit `ping` und `latest`.
Er ist keine Nachbildung eines internen DJI-WebSockets.
