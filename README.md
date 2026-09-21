# M4-Cloud

M4-Cloud ist die lokale Integrations- und Steuerplattform zwischen DJI FlightHub 2, DJI OpenAPI V2, DJI Cloud API und den M4-Anwendungen.

## Status

Neuaufbau ab 21.09.2026 auf `main`.

Die Architektur startet bewusst klein und sauber:

- **FH2 OpenAPI V2**: REST-Adapter zu FlightHub 2 / On-Premises.
- **DJI Cloud API**: separater Geräte-/RC-naher Integrationspfad über MQTT/HTTPS/WebSocket.
- **Control API**: einheitliche interne API und kanonisches M4-Datenmodell.
- **PostgreSQL**: Persistenz.
- **Mosquitto**: interner MQTT-Broker mit Benutzer/ACL.
- **Lyrebird**: deaktiviert und nicht Bestandteil dieses Neuaufbaus.

## Architekturprinzip

```text
FlightHub 2 ── OpenAPI V2 ──┐
                            ├── M4 Control API ── M4-Domainmodell
RC Pro / Aircraft ─ Cloud API ┘         │
                                        ├── PostgreSQL
                                        └── MQTT
```

OpenAPI V2 und Cloud API werden **nicht** vermischt. DJI-spezifische Felder werden an den Adaptergrenzen auf ein stabiles M4-Domainmodell normalisiert.

## Start

```bash
cp .env.example .env
docker compose up --build
curl http://localhost:8080/health
curl http://localhost:8080/ready
curl http://localhost:8080/api/v1/system
```

## Repository-Regeln

- Entwicklungs- und Zielbranch: `main`.
- CI-Konfiguration wird ausschließlich durch den Direktor gepflegt.
- Keine M3-Cloud-Abhängigkeit.
- Keine Lyrebird-Abhängigkeit.
- Keine Secrets im Repository.
- DJI-Integrationen bleiben austauschbare Adapter.
