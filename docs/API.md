# Control API V1

Basis-URL über den Reverse Proxy: `http://<m4-host>:8080`

## System

### `GET /health`

Liveness der Control API.

### `GET /ready`

Prüft PostgreSQL, MQTT und den Heartbeat des Integration Workers. HTTP 503
bedeutet, dass mindestens eine eigene M4-Laufzeitabhängigkeit nicht bereit ist.

### `GET /api/v1/system/status`

Nicht-sensitiver Systemstatus. Passwörter, FH2-Token und konkrete
FH2-Upstream-URL werden nicht ausgegeben.

## DJI FlightHub 2 OpenAPI V2

### `GET /api/v1/fh2/status`

Prüft die V2-Konfiguration und – wenn URL, Token und Organisations-UUID
vorhanden sind – über einen minimalen offiziellen Geräte-GET die OpenAPI.

### `GET /api/v1/fh2/devices`

Parameter: `device_class=airport|drone|base_station`, `page`,
`page_size`.

### `GET /api/v1/fh2/hms`

Mindestens ein `device_sn`. Ohne expliziten Zeitraum werden die letzten
sieben Tage verwendet.

### `GET /api/v1/fh2/waylines`

Read-only Wayline-Liste des konfigurierten Projekts.

### `GET /api/v1/fh2/flight-tasks`

Read-only Task-Liste. Optional: `flight_task_status` und mehrfaches `sn`.

Details und DJI-Upstream-Pfade: `docs/FH2-OPENAPI-V2.md`.

## DJI Kamera-/Videopfad-Erkennung

### `GET /api/v1/cameras/status`

Zeigt ausschließlich nicht-sensitive Konfigurationsinformationen zur
Kameraerkennung. Die Cloud-API-Basis-URL und der Token werden nicht ausgegeben.

### `GET /api/v1/cameras/paths`

Liest die aktuell verfügbaren Kamera-/Videopfade read-only aus der offiziellen
DJI-Cloud-API-Capacity-Ressource:

```http
GET /manage/api/v1/live/capacity
x-auth-token: <access_token>
```

M4 normalisiert daraus unter anderem:

- `device_sn`
- `camera_index`
- `video_index`
- `video_type`
- `switchable_video_types`
- `video_id`

Beispiel für die von DJI verwendete Video-ID-Struktur:

```text
<drone-sn>/<payload-index>/<video-index>
1581ABC/67-0-0/normal-0
```

Details: `docs/CAMERA-PATHS.md`.

## Ereignisse

### `POST /api/v1/events`

Neutraler HTTP-/Webhook-Eingang.

### `GET /api/v1/events?limit=100`

Letzte persistierte Integrationsereignisse, Limit 1–500.

### `WS /ws/events`

M4-WebSocket mit:

- `ping` -> `pong`
- `latest` -> letzte 50 Ereignisse

## Entwickler

### `GET /api/docs`

Swagger UI.

### `GET /api/openapi.json`

OpenAPI-Schema.

### `GET /metrics`

Prometheus-Metriken; nicht im öffentlichen API-Schema gelistet.
