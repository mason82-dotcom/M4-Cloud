# DJI FlightHub 2 Integration

## Zweck

M4-Cloud ergänzt eine offiziell bereitgestellte DJI FlightHub 2
On-Premises-Installation. Das Repository enthält **keine** FlightHub-2-
Serverbinärdateien und versucht nicht, DJI-interne Dienste nachzubilden.

## Unterstützte Integrationswege

Die Architektur bereitet die von DJI öffentlich beschriebenen
Integrationsklassen vor:

- HTTPS / REST / FlightHub OpenAPI
- MQTT
- WebSocket
- FlightHub Sync / dateibasierte Übergaben
- Livestream-Weiterleitung bleibt Aufgabe der offiziellen FH2-/Sync-
  Konfiguration; M4 terminiert in V1 keinen proprietären DJI-Videostream.

## FH2 OpenAPI

Setzen:

```env
FH2_UPSTREAM_BASE_URL=https://fh2.example.local
FH2_API_TOKEN=...
FH2_UPSTREAM_VERIFY_TLS=true
```

`GET /api/v1/fh2/status` prüft die grundsätzliche Erreichbarkeit, ohne die
URL oder den Token in der API-Antwort preiszugeben.

V1 nimmt absichtlich **keine undokumentierten OpenAPI-Pfade** an. Sobald für
die eingesetzte FH2-Version die offizielle OpenAPI-Definition vorliegt, werden
deren konkreten Ressourcen im Adapter ergänzt. Damit vermeiden wir falsche oder
versionsabhängige DJI-Endpunkte.

## MQTT

Der Worker abonniert die in `DJI_MQTT_TOPICS` konfigurierten Topics und
persistiert empfangene Ereignisse. Standard ist ausschließlich
`m4/fh2/#`; die tatsächlichen DJI-Topics werden erst entsprechend der
offiziellen Cloud-API-/FH2-Konfiguration eingetragen.

## HTTP-Events

`POST /api/v1/events` ist ein neutraler Webhook-Eingang für offiziell
konfigurierte FH2-/Sync-Ereignisse oder eigene Adapter.

## WebSocket

`/ws/events` bietet einen M4-eigenen Live-Kanal. Unterstützte Befehle:

- `ping`
- `latest`

Der Kanal ist keine Nachbildung eines internen DJI-WebSockets.
