# Betrieb

## Podman + Quadlet

Empfohlener WSL2-/Linux-Pfad:

```bash
cd ~/src/M4-Cloud
cp -n .env.example .env
chmod 600 .env
nano .env
# POSTGRES_PASSWORD setzen

./scripts/m4-manager.sh install
./scripts/m4-manager.sh start
./scripts/m4-manager.sh verify
```

Die lokale Abnahme prüft unter anderem:

- Health/Readiness
- FH2-Routen
- DJI-Cloud-Status
- Kamera-/Telemetry-Routen
- Anonymous MQTT wird abgewiesen
- authentifizierter MQTT-Zugriff funktioniert
- HTTP -> PostgreSQL
- MQTT -> Worker -> PostgreSQL

## Manager

```bash
./scripts/m4-manager.sh status
./scripts/m4-manager.sh logs
./scripts/m4-manager.sh dji-cloud-status
./scripts/m4-manager.sh camera-status
./scripts/m4-manager.sh camera-paths
./scripts/m4-manager.sh camera-telemetry
./scripts/m4-manager.sh fh2-status
./scripts/m4-manager.sh fh2-verify
```

## Docker Compose

Compose bleibt als Referenzpfad erhalten.

`.env` benötigt mindestens:

```env
POSTGRES_PASSWORD=...
MQTT_WORKER_PASSWORD=...
MQTT_HEALTH_PASSWORD=...
```

## Director Validation

Die zentrale GitHub-Actions-Validation ist ausschließlich Sache des Direktors.

Workflow:

```text
workflow_dispatch
```

Manager, RC Pro und Multispektral starten keine CI-Läufe.

## Monitoring

```bash
./scripts/m4-manager.sh monitoring-start
./scripts/m4-manager.sh monitoring-status
```

## Update

```bash
git pull --ff-only
./scripts/m4-manager.sh install
./scripts/m4-manager.sh restart
./scripts/m4-manager.sh verify
```

## Diagnose

```bash
./scripts/m4-manager.sh status
journalctl --user -u mqtt.service -n 200 --no-pager
journalctl --user -u control-api.service -n 200 --no-pager
journalctl --user -u integration-worker.service -n 200 --no-pager
curl -s http://127.0.0.1:8080/api/v1/system/status | jq
curl -s http://127.0.0.1:8080/api/v1/dji/cloud/status | jq
curl -s http://127.0.0.1:8080/api/v1/fh2/status | jq
```
