# M4-Cloud

Eigenständiger Integrations- und Kontrollserver für **DJI FlightHub 2 On-Premises**.

> M4-Cloud ist vollständig unabhängig von M3-Cloud. Proprietäre DJI-FlightHub-2-Komponenten werden nicht nachgebaut, kopiert oder redistribuiert. Das offiziell bereitgestellte/lizenzierte FH2-On-Premises-System bzw. DJI FH2 AIO bleibt der DJI-Upstream.

## V1.0

M4-Cloud V1 stellt die vollständige eigene Integrations- und Betriebsschicht bereit:

- Docker-Compose-Deployment
- Nginx Reverse Proxy
- FastAPI Control API
- PostgreSQL-Persistenz
- MQTT-Broker
- MQTT-Integration-Worker\n- optionaler DJI-Cloud-API-MQTT-Ingest
- HTTPS/FH2-Upstream-Adapter
- WebSocket-Ereigniskanal
- neutraler HTTP-Webhook-Eingang
- Prometheus-Metriken und optionaler Prometheus-Dienst
- Health-/Readiness-Prüfungen
- Backup-/Restore-Runbook
- CI-End-to-End-Abnahme

## Schnellstart

```bash
cp .env.example .env
# POSTGRES_PASSWORD in .env ändern
docker compose up -d --build

curl http://localhost:8080/health
curl http://localhost:8080/ready
curl http://localhost:8080/api/v1/system/status
curl http://localhost:8080/api/v1/fh2/status
```

Vollständige lokale Abnahme unter Linux/WSL2:

```bash
sh scripts/verify.sh
```

Unter Windows PowerShell:

```powershell
.\scripts\verify.ps1
```

Für WSL2 + Ubuntu + das neue Microsoft-WSLC siehe `docs/SETUP-WSL2-WSLC.md`.

## Dienste

| Dienst | Aufgabe | Host-Port |
| --- | --- | --- |
| `reverse-proxy` | HTTP/API/WebSocket-Einstieg | 8080 |
| `control-api` | M4-Control- und Integrations-API | intern |
| `integration-worker` | MQTT-Ereignisse -> PostgreSQL | intern |
| `postgres` | M4-eigene Persistenz | intern |
| `mqtt` | MQTT-Integrationspunkt | 127.0.0.1:1883 |
| `prometheus` | optionales Monitoring-Profil | 127.0.0.1:9090 |

## DJI FlightHub 2 anbinden

In `.env`:

```env
FH2_UPSTREAM_BASE_URL=https://fh2.example.local
FH2_API_TOKEN=...
FH2_UPSTREAM_VERIFY_TLS=true
```

Die konkrete FlightHub-OpenAPI unterscheidet sich nach DJI-Version und
On-Premises-Ausprägung. M4 erfindet deshalb keine undokumentierten DJI-Pfade.
Konkrete Ressourcen werden gegen die offizielle OpenAPI der eingesetzten
FH2-Version angebunden.

Für generische/FH2-MQTT-Topics wird `DJI_MQTT_TOPICS` verwendet. Der direkte
DJI-Cloud-API-Pfad wird getrennt über `DJI_CLOUD_API_ENABLED` und
`DJI_CLOUD_API_TOPICS` aktiviert.

## Dokumentation

- `docs/ARCHITECTURE.md` – Systemgrenzen und Komponenten
- `docs/DJI-INTEGRATION.md` – DJI/FH2-Anbindung
- `docs/API.md` – Control API
- `docs/NETWORK.md` – Ports und Netzwerk
- `docs/OPERATIONS.md` – Betrieb, Monitoring, Backup und Restore
- `docs/SETUP-WSL2-WSLC.md` – Windows 11, WSL2, Ubuntu, VS Code und WSLC\n- `docs/SETUP-PODMAN-QUADLET.md` – Docker-Desktop-freier Betrieb mit Podman und Quadlet
- `SECURITY.md` – Sicherheitsvorgaben
