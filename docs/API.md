# Control API V1

Basis-URL über den Reverse Proxy: `http://<m4-host>:8080`

## `GET /health`

Liveness des Control-API-Prozesses.

## `GET /ready`

Prüft die eigene Laufzeitkette:

- PostgreSQL
- MQTT
- frischen Heartbeat des Integration Workers

HTTP 503 bedeutet, dass mindestens eine V1-Abhängigkeit noch nicht betriebsbereit ist.

## `GET /api/v1/system/status`

Nicht-sensitiver Systemstatus. Passwörter, API-Tokens und die konkrete
FH2-Upstream-URL werden nicht ausgegeben.

## `GET /api/v1/fh2/status`

Prüft, ob der konfigurierte FH2-Upstream grundsätzlich erreichbar ist.
Ohne Konfiguration wird `reason=not_configured` zurückgegeben. Ein HTTP-Status
wie 401 kann trotzdem bedeuten, dass der Server netzseitig erreichbar ist.

## `POST /api/v1/events`

Neutraler HTTP-/Webhook-Eingang für Integrationsereignisse.

Beispiel:

```json
{
  "source": "fh2",
  "topic": "mission/status",
  "payload": {"state": "finished"}
}
```

## `GET /api/v1/events?limit=100`

Liefert die zuletzt persistierten Integrationsereignisse. Zulässiger Bereich:
1 bis 500.

## `WS /ws/events`

M4-eigener WebSocket-Kanal. Befehle:

- `ping` -> `pong`
- `latest` -> letzte 50 Ereignisse

## `GET /api/docs`

Swagger UI.

## Intern: `GET /metrics`

Prometheus-Metriken der Control API. Der optionale Prometheus-Container greift
direkt im Compose-Netz darauf zu.
