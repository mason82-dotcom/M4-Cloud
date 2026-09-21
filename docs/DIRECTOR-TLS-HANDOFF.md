# Direktor-Handoff: MQTT-TLS Follow-up

Branch:

```text
agent/director-mqtt-tls
```

Basis:

```text
agent/director-candidate-v2b
```

## Ziel

Optionalen externen MQTT-TLS-Listener auf Port 8883 vorbereiten, ohne den
internen Port 1883 oder die bestehenden ACLs zu verändern.

## Eigenschaften

- TLS standardmäßig aus
- Aktivierung nur über `docker-compose.tls.yml`
- Port 1883 bleibt Host-Loopback
- Port 8883 wird erst mit Overlay veröffentlicht
- Zertifikat und Key über Compose Secrets
- TLS mindestens 1.2
- keine Client-Zertifikatspflicht
- MQTT Username/Password + ACL bleiben aktiv
- DRC bleibt gesperrt
- Bootstrap meldet `mqtt.tls=true`
- Bootstrap liefert weiterhin kein MQTT-Passwort

## Lokale Prüfung

```bash
cd services/control-api
ruff check app tests
pytest -q

cd ../..
docker compose config
./scripts/verify-tls-config.sh
```

Mit realem Zertifikat kann der Direktor anschließend bewusst den TLS-Stack
starten und den Handshake mit `openssl s_client` prüfen.

Die zentrale GitHub-Actions-CI wird weiterhin ausschließlich vom Direktor
gestartet.
