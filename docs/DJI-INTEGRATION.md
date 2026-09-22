# DJI-Integration in M4-Cloud V2.0

## Grundsatz

FlightHub 2 OpenAPI V2 und DJI Cloud API bleiben getrennte Adapterpfade.

M4 führt beide Pfade nur über das kanonische interne Domainmodell zusammen.
Lyrebird ist deaktiviert.

## FlightHub 2 / OpenAPI V2

Der FH2-Adapter arbeitet read-only und injiziert zentral:

- `X-User-Token`
- `X-Project-Uuid` bei projektbezogenen Aufrufen
- `X-Request-Id`
- `X-Language`

Implementierte Ressourcen:

- Geräte: `/openapi/v2.0/manage/api/v1/organizations/{orgId}/manage-devices`
- Flugaufgaben: `/openapi/v2.0/task/api/v2/workspaces/{projectId}/flight-tasks`
- Waylines: `/openapi/v2.0/wayline/api/v1/workspaces/{projectId}/web-waylines`

M4 akzeptiert nur 2xx als erfolgreichen HTTP-Status. DJI-Businessfehler mit
`code != 0` werden ebenfalls als Fehler behandelt.

M4-Endpunkte:

```text
GET /api/v1/fh2/status
GET /api/v1/fh2/devices
GET /api/v1/fh2/waylines
GET /api/v1/fh2/flight-tasks
```

## DJI Cloud API HTTP

Die Kameraerkennung nutzt read-only:

```http
GET /manage/api/v1/live/capacity
x-auth-token: <access_token>
```

M4 normalisiert die Antwort auf stabile Kamera-/Videoobjekte.

Video-ID:

```text
<device_sn>/<payload_index>/<video_index>
```

Beispiel:

```text
DRONE1/67-0-0/normal-0
```

M4-Endpunkte:

```text
GET /api/v1/cameras/status
GET /api/v1/cameras/paths
```

## DJI Cloud API MQTT

Mosquitto läuft mit:

```text
allow_anonymous false
```

Es existieren zwei getrennte Rollen.

### M4-Service

Der interne M4-Benutzer darf:

- `m4/#` lesen/schreiben
- DJI Status/State/OSD/Requests/Events/Replies lesen
- keine DJI-Gerätekommandos publizieren
- `$SYS/#` für Brokerdiagnose lesen

### DJI-/RC-Client

Der externe DJI-/RC-Benutzer darf:

- `sys/product/+/status` publizieren
- `thing/product/+/state` publizieren
- `thing/product/+/osd` publizieren
- `thing/product/+/requests` publizieren
- `thing/product/+/events` publizieren
- `thing/product/+/services_reply` publizieren
- `thing/product/+/property/set_reply` publizieren
- `thing/product/+/services` abonnieren
- `thing/product/+/property/set` abonnieren

Diese Topic-Klassen folgen dem offiziellen DJI Cloud API Demo als
Protokollreferenz.

## Bootstrap-Descriptor

M4 stellt einen geschützten Bootstrap bereit:

```http
GET /api/v1/cloud/bootstrap
X-M4-Bootstrap-Token: <DJI_BOOTSTRAP_TOKEN>
```

Ohne konfigurierten Token antwortet M4 mit HTTP 503. Ein fehlender oder falscher
Header wird mit HTTP 401 abgewiesen. Erst nach erfolgreicher Authentifizierung
werden MQTT-Host, Port, Benutzername, MQTT-Passwort und Topic-Klassen geliefert.
DRC bleibt deaktiviert.

## DRC und Flugsteuerung

In V2.0 nicht freigegeben:

```text
thing/product/+/drc/up
thing/product/+/drc/down
```

Ebenfalls nicht Bestandteil von V2.0:

- Aircraft Control
- RTH
- Missionsstart
- Payload Control
- Kamera-Fernsteuerung

## Kamera- und Multispektralmodell

M4 nutzt unter anderem:

- `device_sn`
- `payload_index`
- `video_index`
- `video_type`
- `video_id`
- `lens_index`
- `live_source`
- `zoom_factor`
- `focal_length_mm`
- `iso`
- `shutter_speed`
- Gimbal Pitch/Roll/Yaw

Multispektral-spezifische Band-, Irradiance- und Kalibrierungsfelder werden
erst nach den delegierten Fachpaketen #14, #16 und #15 finalisiert. V2.0
erfindet dafür keine sensorabhängigen Werte.
