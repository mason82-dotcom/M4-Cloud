# Direktor-Handoff V2.0

## Kandidat

```text
agent/director-candidate-v2b
```

Dieser Branch ist ausschließlich als Zuarbeit für den Direktor gedacht.

Der Manager startet **keine** GitHub-Actions-CI. Der vorhandene Workflow bleibt
manuell über `workflow_dispatch`.

## Inhalt des Kandidaten

Die V2.0-Basis besitzt bereits:

- getrennte FH2-OpenAPI-V2- und DJI-Cloud-API-Adapter
- authentifizierten Mosquitto-Broker
- dynamisch erzeugte Password-/ACL-Dateien
- getrennte M4- und DJI-/RC-Benutzer
- DRC explizit nicht freigegeben
- authentifizierte MQTT-Readiness
- read-only DJI-Kamera-Capacity
- read-only FH2-Geräte, Waylines und Flight Tasks

Dieser Kandidat verschärft nur die Defaults:

```env
MQTT_BIND=127.0.0.1
MQTT_PUBLIC_HOST=127.0.0.1
DJI_CLOUD_API_ENABLED=false
```

Damit wird Port 1883 nicht versehentlich unverschlüsselt im LAN veröffentlicht.

## Lokale Zuarbeit vor Director-CI

Manager/Fachagenten dürfen lokal ausführen:

```bash
cd services/control-api
ruff check app tests
pytest -q

cd ../..
docker compose config
./scripts/verify.sh
```

`verify.sh` prüft zusätzlich, dass anonymer MQTT-Zugriff abgewiesen wird.

## Director-Prüfpunkte

Wenn der Direktor den manuellen CI-Lauf startet:

1. Ruff/Pytest grün
2. keine Secret-Ausgabe über `/api/v1/system`
3. `/api/v1/cloud/bootstrap` enthält kein MQTT-Passwort
4. Anonymous MQTT wird abgewiesen
5. M4-Service-Credentials funktionieren
6. DJI-/RC-Credentials funktionieren nur auf erlaubten ACL-Topics
7. DRC bleibt gesperrt
8. FH2-Adapter bleibt read-only
9. DJI-Kamera-Capacity bleibt read-only

## Noch nicht produktionsbereit für Pilot 2

Vor externer RC-Pro-/Pilot-2-Freigabe fehlen:

- separater MQTT-TLS-Listener
- Zertifikat-/Trust-Chain-Test mit realer Pilot-2-Version
- H5-/JSBridge-Login
- License Verify
- sichere Session/Credential-Ausgabe
- WebSocket-Authentifizierung
- dynamische RC-/Device-spezifische ACLs
- Gerätekommandos
- DRC

## Bewusste LAN-Testfreigabe

Nur für einen kontrollierten Test:

```env
MQTT_BIND=0.0.0.0
MQTT_PUBLIC_HOST=<IP-des-M4-Hosts>
DJI_CLOUD_API_ENABLED=true
```

Das ist ohne TLS **kein** Produktionsmodus.
