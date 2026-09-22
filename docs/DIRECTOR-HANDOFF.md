# Director Handoff: DJI Bootstrap Security

## Kandidat

Branch:

```text
agent/director-bootstrap-security-v2
```

Ziel: kleine Security-Härtung auf dem aktuellen M4-Cloud-V2.0-`main`.

## Änderungen

- `DJI_BOOTSTRAP_TOKEN` als geheimes Setting
- `GET /api/v1/cloud/bootstrap` mit `X-M4-Bootstrap-Token` geschützt
- MQTT-Passwort wird erst nach erfolgreicher Bootstrap-Authentifizierung ausgegeben
- Unit-Tests für 503/401/200-Bootstrap-Verhalten
- M4-Service verliert ungenutzte DJI-Command-Schreibrechte
- Referenz-ACL und dynamische Compose-ACL bleiben synchron
- lokale `verify.sh` prüft Bootstrap-Schutz und Anonymous-MQTT-Ablehnung
- Dokumentation der verbleibenden TLS-Grenze

DRC bleibt deaktiviert.

## Lokale Vorprüfung vor Director CI

```bash
git switch agent/director-bootstrap-security-v2
git pull --ff-only
cp -n .env.example .env
```

In `.env` mindestens sichere Werte setzen:

```env
POSTGRES_PASSWORD=...
MQTT_SERVICE_PASSWORD=...
DJI_MQTT_PASSWORD=...
DJI_BOOTSTRAP_TOKEN=...
MQTT_PUBLIC_HOST=<M4-LAN-IP>
```

Dann:

```bash
./scripts/verify.sh
```

Erwartet:

- `/ready` meldet PostgreSQL und authentifiziertes MQTT bereit
- falscher Bootstrap-Token wird abgewiesen
- korrekter Bootstrap-Token funktioniert
- anonymer MQTT-Publish wird abgewiesen
- M4- und DJI-MQTT-Rollen funktionieren

## Director CI

Nur der Direktor startet:

```text
.github/workflows/validate.yml
workflow_dispatch
```

Manager, RC Pro und Multispektral starten keine CI.

## Bekannte Restgrenze

MQTT ist auf Port 1883 noch nicht TLS-verschlüsselt. Der Stand ist damit für
das vertrauenswürdige LAN vorgesehen, nicht für WAN/Internet. Der nächste
Security-Baustein ist ein separater MQTT-TLS-Listener.
