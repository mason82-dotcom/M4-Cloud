# Architektur

## Getrennte DJI-Pfade

```text
DJI Pilot 2 / Dock
       |
 MQTT / HTTPS / WS
       v
+-----------------------+
| DJI Cloud API Adapter |
+-----------+-----------+
            |
            v
        M4 intern
            ^
            |
+-----------+-----------+
| FH2 OpenAPI V2 Client |
+-----------------------+
            ^
            |
FlightHub 2 Privatization
```

### DJI Cloud API

M4 ist der eingehende Integrationsserver.

Aktuell:

- MQTT-Ingest
- Auth/ACL
- Pilot-2-Bootstrap
- Live-Capacity/Kamerapfade
- Kamera-/Gimbal-Telemetrie
- eigener M4-WebSocket

Noch nicht:

- externer MQTT-TLS-Listener
- Pilot-2-H5-/JSBridge-Seite
- Cloud-API-HTTPS-Module vollständig
- Gerätekommandos
- DRC

### FH2 Privatization OpenAPI V2

M4 ist read-only Client eines vorhandenen DJI-FH2-Servers.

Aktuell:

- Geräte
- HMS
- Waylines
- Flight Tasks

Authentifizierung, Fehlersemantik und Transport bleiben strikt vom Cloud-API-Ingress getrennt.

## Eigene Komponenten

- Reverse Proxy
- Control API
- PostgreSQL
- gehärteter Mosquitto
- MQTT Integration Worker
- Prometheus

## Runtime

### Podman + Quadlet

Empfohlener lokaler WSL2-/Linux-Pfad.

### Docker Compose

Referenzpfad und Basis für die vom Direktor manuell gestartete Validation.

### WSLC

Optional/experimentell, nicht primäre Multi-Service-Runtime.

## Datenmodell

Beide DJI-Pfade dürfen oberhalb ihrer Adapter gemeinsame M4-Ereignis-/Persistenzmodelle verwenden. Adapter-spezifische Authentifizierung und Fehlercodes werden nicht vermischt.
