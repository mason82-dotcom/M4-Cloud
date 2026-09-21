# M4-Cloud

Eigenständiger Integrations- und Kontrollserver für **DJI FlightHub 2 On-Premises**.

> M4-Cloud ist bewusst unabhängig von M3-Cloud. Proprietäre DJI-FlightHub-2-Komponenten werden nicht nachgebaut, kopiert oder redistribuiert. Ein offiziell bereitgestelltes/lizenziertes FH2-On-Premises-System wird als externer Upstream behandelt.

## Ziel V1

- reproduzierbarer Docker-Compose-Start
- lokaler Reverse Proxy
- M4-Control-API mit Health-/Readiness-Endpunkten
- PostgreSQL für M4-eigene Persistenz
- MQTT als vorbereiteter Integrationskanal
- dokumentierte HTTPS/WebSocket/MQTT-Integrationspunkte
- klare Grenze zwischen DJI-Upstream und M4-eigenen Diensten
- Konfiguration über Umgebungsvariablen/Secrets
- Bereitstellung im Heim-/LAN-Netz

## Schnellstart

```bash
cp .env.example .env
# POSTGRES_PASSWORD in .env setzen
docker compose up -d --build
curl http://localhost:8080/health
curl http://localhost:8080/api/v1/system/status
```

## Dienste

| Dienst | Aufgabe | Standard |
| --- | --- | --- |
| `reverse-proxy` | zentraler HTTP-Einstieg | TCP 8080 |
| `control-api` | M4-Control-/Integrations-API | nur Compose-Netz |
| `postgres` | M4-eigene Persistenz | nur Compose-Netz |
| `mqtt` | vorbereiteter MQTT-Integrationspunkt | Host 127.0.0.1:1883 |

Der MQTT-Port ist absichtlich nur an Loopback gebunden. Für DJI-Geräte im LAN darf er erst nach Aktivierung von Authentifizierung/TLS auf eine LAN-Adresse gebunden werden.

## DJI-Upstream

`FH2_UPSTREAM_BASE_URL` verweist optional auf eine offiziell bereitgestellte FH2-On-Premises-Instanz. M4-Cloud muss auch ohne erreichbaren Upstream startfähig und diagnostizierbar bleiben.

Siehe `docs/ARCHITECTURE.md` und `docs/NETWORK.md`.
