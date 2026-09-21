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

Der Basisstand definiert zunächst nur die Integrationsgrenze. Bootstrap-Authentifizierung, Gerätecredentials und dynamische ACLs folgen als eigener Baustein.

## Kamera und Gimbal

Intern nutzt M4 stabile Felder wie `payload_index`, `lens_index`, `live_source`, `zoom_factor`, `focal_length_mm`, `pitch_deg`, `roll_deg` und `yaw_deg`.

Mavic 3E, Mavic 3T und Multispektral werden über Adapter-Mappings auf dasselbe Domainmodell geführt.
