# DJI-Integration

## FlightHub 2 / OpenAPI V2

Der FH2-Adapter injiziert zentral:

- `x-user-token`
- `X-Project-Uuid`
- `X-Request-Id`
- `X-Language`

Initiale Ressourcen:

- Geräte: `/openapi/v2.0/manage/api/v1/organizations/{orgId}/manage-devices`
- Flugaufgaben: `/openapi/v2.0/task/api/v2/workspaces/{projectId}/flight-tasks`
- Waylines: `/openapi/v2.0/wayline/api/v1/workspaces/{projectId}/web-waylines`

Weitere V2-Endpunkte werden ausschließlich im FH2-Adapter ergänzt.

## DJI Cloud API

Die Cloud API bleibt ein eigener Adapter. MQTT, HTTPS und WebSocket werden nicht in den FH2-Client eingebaut.

Der Basisstand trennt Cloud API und FH2 strikt. MQTT nutzt getrennte M4-/DJI-Credentials und ACLs. Der Bootstrap ist über `X-M4-Bootstrap-Token` geschützt und gibt das DJI-MQTT-Passwort nur nach erfolgreicher Bootstrap-Authentifizierung aus. DRC und aktive Gerätekommandos bleiben deaktiviert.

### Pilot-2-Bootstrap

```http
GET /api/v1/cloud/bootstrap
X-M4-Bootstrap-Token: <DJI_BOOTSTRAP_TOKEN>
```

Ohne konfigurierten Bootstrap-Token antwortet M4 mit HTTP 503, bei falschem
Token mit HTTP 401. Erst ein gültiger Token liefert die MQTT-Zugangsdaten für
den DJI-/RC-Client.

Der Bootstrap ist noch kein vollständiger Pilot-2-H5-Login. Vor WAN-Nutzung
sind HTTPS und ein externer MQTT-TLS-Pfad erforderlich.

## Kamera und Gimbal

Intern nutzt M4 stabile Felder wie `payload_index`, `lens_index`, `live_source`, `zoom_factor`, `focal_length_mm`, `pitch_deg`, `roll_deg` und `yaw_deg`.

Mavic 3E, Mavic 3T und Multispektral werden über Adapter-Mappings auf dasselbe Domainmodell geführt.
