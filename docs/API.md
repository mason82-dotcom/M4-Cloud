# Control API

Basis-URL:

```text
http://<m4-host>:8080
```

## System

### `GET /health`

Liveness.

### `GET /ready`

Prüft PostgreSQL, MQTT und Worker-Heartbeat.

### `GET /api/v1/system/status`

Nicht-sensitiver Gesamtstatus. Secrets und konkrete Upstream-URLs werden nicht ausgegeben.

## DJI Cloud API Ingress

### `GET /api/v1/dji/cloud/status`

Liefert:

- Aktivierungsstatus
- MQTT-Erreichbarkeit
- Bootstrap-Bereitschaft
- aktive DJI-Uplink-Subscriptions
- Capability-Flags

Gerätekommandos und DRC stehen auf `false`.

### `GET /api/v1/dji/cloud/bootstrap`

M4-eigener Pilot-2-Bootstrap.

Header:

```text
X-M4-Bootstrap-Token: <DJI_BOOTSTRAP_TOKEN>
```

Mögliche Antworten:

- `401 invalid_bootstrap_token`
- `503 dji_cloud_api_disabled`
- `503 dji_cloud_bootstrap_incomplete`
- `200` mit Platform-, Workspace-, Lizenz-, API-, WS- und MQTT-Konfiguration

## Kamera und Gimbal

### `GET /api/v1/cameras/status`

Nicht-sensitiver Status der dynamischen Kameraerkennung.

### `GET /api/v1/cameras/paths`

Liest read-only die DJI-Ressource:

```text
GET /manage/api/v1/live/capacity
x-auth-token: <access_token>
```

und normalisiert unter anderem:

- `device_sn`
- `camera_index`
- `video_index`
- `video_type`
- `switchable_video_types`
- `video_id`

### `GET /api/v1/cameras/telemetry`

Normalisiert Kamera-/Gimbal-Telemetrie aus zuletzt persistierten DJI-MQTT-Events. Der Endpoint ist read-only.

## FlightHub 2 Privatization OpenAPI V2

### `GET /api/v1/fh2/status`
### `GET /api/v1/fh2/devices`
### `GET /api/v1/fh2/hms`
### `GET /api/v1/fh2/waylines`
### `GET /api/v1/fh2/flight-tasks`

Details: `docs/FH2-OPENAPI-V2.md`.

## Ereignisse

### `POST /api/v1/events`

Neutraler HTTP-/Webhook-Eingang.

### `GET /api/v1/events?limit=100`

Letzte persistierte Integrationsereignisse. Limit 1–500.

DJI-MQTT-Topics werden als `source=dji-cloud-api` klassifiziert.

## WebSocket

### `WS /ws/events`

M4-eigener Event-WebSocket:

- `ping`
- `latest`

Dieser Endpoint ist nicht der spätere DJI-Pilot-2-WebSocket.

## Entwickler

- `GET /api/docs`
- `GET /api/openapi.json`
- `GET /metrics`
