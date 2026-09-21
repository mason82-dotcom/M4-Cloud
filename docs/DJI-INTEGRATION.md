# DJI-Integration

## Grundsatz

M4-Cloud führt zwei DJI-Pfade zusammen, ohne sie technisch zu vermischen.

## 1. DJI Cloud API: Pilot 2 / Dock -> M4

Transporte:

- MQTT
- HTTPS
- WebSocket
- JSBridge in Pilot 2 H5

### MQTT-Uplinks

```text
thing/product/{device_sn}/osd
thing/product/{device_sn}/state
thing/product/{gateway_sn}/services_reply
thing/product/{gateway_sn}/events
thing/product/{gateway_sn}/requests
thing/product/{gateway_sn}/property/set_reply
sys/product/{gateway_sn}/status
```

M4 klassifiziert diese Ereignisse als `dji-cloud-api`.

DRC wird nicht abonniert/freigegeben.

### MQTT-Downlinks, für Pilot lesbar

```text
thing/product/{gateway_sn}/services
thing/product/{gateway_sn}/events_reply
thing/product/{gateway_sn}/requests_reply
thing/product/{gateway_sn}/property/set
sys/product/{gateway_sn}/status_reply
```

Die Control API erzeugt aktuell keine Gerätekommandos.

### Bootstrap

```text
GET /api/v1/dji/cloud/bootstrap
X-M4-Bootstrap-Token: <DJI_BOOTSTRAP_TOKEN>
```

Der Endpoint ist M4-eigen und liefert die Parameter, die eine spätere H5-Seite an DJI Pilot 2/JSBridge weitergibt.

Relevante spätere JSBridge-Funktionen:

```text
platformVerifyLicense(...)
platformSetWorkspaceId(...)
platformGetRemoteControllerSN()
platformGetAircraftSN()
platformLoadComponent(...)
thingConnect(...)
apiSetToken(...)
wsConnect(...)
```

### Kamera-/Live-Capacity

Read-only:

```text
GET /manage/api/v1/live/capacity
x-auth-token: <access_token>
```

M4 bietet:

```text
GET /api/v1/cameras/status
GET /api/v1/cameras/paths
GET /api/v1/cameras/telemetry
```

Lyrebird ist dafür nicht erforderlich.

## 2. FlightHub 2 Privatization OpenAPI V2: M4 -> FH2

Authentifizierung:

- `X-User-Token`
- `X-Request-Id`
- `X-Language`
- projektbezogen `X-Project-Uuid`

Read-only M4-Routen:

```text
GET /api/v1/fh2/status
GET /api/v1/fh2/devices
GET /api/v1/fh2/hms
GET /api/v1/fh2/waylines
GET /api/v1/fh2/flight-tasks
```

Details: `docs/FH2-OPENAPI-V2.md`.

## Nächste Cloud-API-Schritte

1. MQTT-TLS-Listener
2. Pilot-2-H5-Einstieg
3. License Verify
4. Thing/API/WS-Module verbinden
5. echte RC Pro Enterprise anbinden
6. Device Topology
7. Map/TSA
8. Media/Wayline
9. erst danach gezielte Write-Operationen
10. DRC separat

## Sicherheitsklassen

- READ: aktuell zulässig
- WRITE: separat absichern
- DANGEROUS: explizite Schutz-/Freigabelogik erforderlich

Direktor allein startet und bewertet CI; Manager und Fachagenten liefern lokale Tests und Dokumentation.
