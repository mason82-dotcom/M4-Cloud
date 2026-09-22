# Director Handoff: Bootstrap Security

Branch: `agent/director-bootstrap-security-v3`

## Lokal prüfen

```bash
git switch agent/director-bootstrap-security-v3
git pull --ff-only
cp -n .env.example .env
# sichere Werte setzen
./scripts/verify.sh
```

Erwartet: Bootstrap 503/401/200 korrekt, Anonymous MQTT abgewiesen, beide
authentifizierten MQTT-Rollen funktionsfähig.

## CI

Nur der Direktor startet `.github/workflows/validate.yml` per
`workflow_dispatch`.

## Danach

Issue #21: externer MQTT-TLS-Listener + Pilot-2-H5/HTTPS.
