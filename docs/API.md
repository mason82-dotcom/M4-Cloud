# Control API V1

Basis-URL über den Reverse Proxy: `http://<m4-host>:8080`

## Endpunkte

### `GET /health`

Liveness des Control-API-Prozesses. Dieser Endpunkt prüft bewusst keine
externen Abhängigkeiten.

### `GET /ready`

Readiness der M4-eigenen Infrastruktur. Prüft TCP-Erreichbarkeit von
PostgreSQL und MQTT. Liefert HTTP 503, solange eine dieser Abhängigkeiten fehlt.

### `GET /api/v1/system/status`

Nicht-sensitiver Systemstatus:

- M4-Version
- ob ein FH2-Upstream konfiguriert ist
- TLS-Verifikationsmodus
- interne MQTT-Zieladresse
- aktivierte HTTPS-/WebSocket-Integrationspunkte

Passwörter, Tokens und die konkrete FH2-Upstream-URL werden nicht ausgegeben.

### `GET /api/docs`

Lokale OpenAPI-/Swagger-Dokumentation der Control API.
