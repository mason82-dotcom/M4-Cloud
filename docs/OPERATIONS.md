# Betrieb

## Start

```bash
cp .env.example .env
# POSTGRES_PASSWORD setzen
docker compose up -d --build
```

## Abnahme

```bash
sh scripts/verify.sh
```

Erwartet werden:

- Reverse Proxy healthy
- Control API healthy
- PostgreSQL healthy
- MQTT healthy
- Integration Worker mit frischem Heartbeat
- `/ready` HTTP 200
- System- und FH2-Status-Endpunkte erreichbar

## Monitoring

Die Control API exportiert Prometheus-Metriken unter `/metrics`.

Optional:

```bash
docker compose --profile monitoring up -d
```

Prometheus wird standardmäßig ausschließlich auf
`127.0.0.1:9090` veröffentlicht.

## Backup

PostgreSQL:

```bash
mkdir -p backups
docker compose exec -T postgres pg_dump -U "${POSTGRES_USER:-m4cloud}" "${POSTGRES_DB:-m4cloud}"   > "backups/m4cloud-$(date +%Y%m%d-%H%M%S).sql"
```

MQTT-Persistenz liegt im Docker-Volume `mqtt-data`. Für vollständige
Host-Backups müssen die Docker-Volumes zusammen mit der `.env` außerhalb
des Git-Repositories gesichert werden.

## Restore PostgreSQL

Nur gegen eine bewusst ausgewählte, leere bzw. kompatible Datenbank ausführen:

```bash
cat backups/<backup>.sql | docker compose exec -T postgres   psql -U "${POSTGRES_USER:-m4cloud}" "${POSTGRES_DB:-m4cloud}"
```

## Update

1. Backup erstellen.
2. Neue Version auschecken.
3. `docker compose pull`
4. `docker compose up -d --build`
5. `sh scripts/verify.sh`
6. Erst nach erfolgreicher Abnahme alte Images bereinigen.

## Fehlerdiagnose

```bash
docker compose ps
docker compose logs --tail=200 reverse-proxy control-api integration-worker postgres mqtt
curl -i http://localhost:8080/health
curl -i http://localhost:8080/ready
curl -s http://localhost:8080/api/v1/fh2/status
```
