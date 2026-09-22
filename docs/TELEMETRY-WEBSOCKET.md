# OSD- und Telemetrie-WebSocket

M4 stellt einen read-only Echtzeitpfad für DJI-Telemetrie bereit.

## Datenfluss

```text
DJI Pilot 2 / Dock
        |
        | MQTT
        v
thing/product/{sn}/osd
thing/product/{sn}/state
thing/product/{gateway_sn}/events
sys/product/{gateway_sn}/status
        |
        v
M4 TelemetryHub
        |
        v
/ws/v1/telemetry
        |
        v
WebUI
```

Der TelemetryHub verwendet ausschließlich die interne M4-MQTT-Identität und
abonniert die vier read-only Topic-Klassen. Er publiziert keine DJI-Befehle.

## Status

```http
GET /api/v1/telemetry/status
```

Beispiel:

```json
{
  "started": true,
  "mqtt_connected": true,
  "subscribers": 1,
  "last_message_at_ms": 1790000000000,
  "topics": [
    "thing/product/+/osd",
    "thing/product/+/state",
    "thing/product/+/events",
    "sys/product/+/status"
  ],
  "read_only": true,
  "drc_enabled": false
}
```

## WebSocket

```text
ws://<m4-host>:8080/ws/v1/telemetry
```

Nach dem Verbindungsaufbau sendet M4 zunächst:

```json
{
  "type": "m4.telemetry.ready",
  "read_only": true,
  "drc_enabled": false
}
```

Anschließend werden normalisierte Events übertragen:

```json
{
  "type": "dji.telemetry",
  "source": "dji_cloud_api",
  "topic": "thing/product/AIRCRAFT123/osd",
  "kind": "osd",
  "device_sn": "AIRCRAFT123",
  "gateway_sn": "RC123",
  "method": null,
  "received_at_ms": 1790000000000,
  "payload": {
    "gateway": "RC123",
    "data": {}
  }
}
```

Die DJI-Payload wird absichtlich unverändert unter `payload` weitergereicht.
Damit gehen beim späteren Normalisieren von Flug-, Akku-, Link-, Kamera- oder
Gimbal-Daten keine herstellerspezifischen Felder verloren.

## Backpressure

Jeder WebSocket-Client erhält eine begrenzte Queue. Wenn ein Browser langsamer
ist als die eingehende Telemetrie, wird das jeweils älteste noch nicht
gesendete Event verworfen. Dadurch blockiert ein langsamer Browser weder MQTT
noch andere WebSocket-Clients.

## DRC-Grenze

Dieser Baustein:

- publiziert nicht nach `services`
- publiziert nicht nach `property/set`
- publiziert nicht nach `drc/down`
- abonniert nicht `drc/up`
- aktiviert keine Flugsteuerung

DRC bleibt eine getrennte spätere Sicherheitsdomäne.

## Produktionsgrenze

Der aktuelle WebSocket besitzt noch keine WebUI-Session-Authentifizierung.
Daher ist er für den kontrollierten Entwicklungs-/LAN-Betrieb gedacht und
darf nicht ungeschützt ins Internet veröffentlicht werden. Vor externer
Nutzung sind HTTPS/WSS und WebUI-Session-Authentifizierung erforderlich.
