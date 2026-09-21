# Sicherheit

## Aktive Defaults

- keine Secrets im Repository
- PostgreSQL ohne Host-Port
- Control API nur hinter Reverse Proxy
- MQTT am Host standardmäßig nur `127.0.0.1:1883`
- anonymer MQTT-Zugriff deaktiviert
- Prometheus nur `127.0.0.1:9090`
- FH2-TLS-Verifikation standardmäßig aktiv
- keine Gerätekommandos
- kein DRC

## MQTT-Rollen

### m4-worker

Liest M4-/DJI-Uplink-Topics und persistiert Ereignisse.

### m4-health

Darf nur definierte Health-/Verify-/CI-Testtopics verwenden.

### dji-pilot

Wird nur bei aktivierter DJI Cloud API angelegt.

Erlaubtes Schreiben:

```text
thing/product/+/osd
thing/product/+/state
thing/product/+/services_reply
thing/product/+/events
thing/product/+/requests
thing/product/+/property/set_reply
sys/product/+/status
```

Erlaubtes Lesen:

```text
thing/product/+/services
thing/product/+/events_reply
thing/product/+/requests_reply
thing/product/+/property/set
sys/product/+/status_reply
```

DRC ist nicht freigegeben.

## Bootstrap

`GET /api/v1/dji/cloud/bootstrap` verlangt:

```text
X-M4-Bootstrap-Token: <DJI_BOOTSTRAP_TOKEN>
```

Die Antwort kann App-ID, App-Key, License, API-/WS-Token und MQTT-Credentials enthalten. Deshalb gilt:

- nicht öffentlich über HTTP bereitstellen
- nicht loggen
- nur über kontrollierte H5-/Login-Session verwenden
- vor realer Pilot-2-Anbindung HTTPS aktivieren

## Lokale Secret-Erzeugung

Der Quadlet-Installer erzeugt fehlende Werte lokal für:

- `MQTT_WORKER_PASSWORD`
- `MQTT_HEALTH_PASSWORD`
- `DJI_BOOTSTRAP_TOKEN`
- `DJI_API_TOKEN`
- `DJI_WS_TOKEN`
- `DJI_MQTT_PASSWORD`
- `DJI_WORKSPACE_ID`

Nicht automatisch erzeugt werden:

- `DJI_APP_ID`
- `DJI_APP_KEY`
- `DJI_APP_LICENSE`

## Vor externer Pilot-2-/Dock-Anbindung

Erforderlich:

1. separater MQTT-TLS-Listener
2. Serverzertifikat/Trust-Chain
3. bewusst konfigurierte externe Broker-Adresse
4. HTTPS für H5 und Bootstrap
5. Benutzer-/Session-Authentifizierung
6. Firewall-Begrenzung
7. Credential-Rotation
8. DRC nur mit eigener, zeitlich begrenzter Sessionlogik

Username/Passwort auf unverschlüsseltem MQTT ist kein Produktionszugang.

## FH2 Privatization

FH2-Zugangsdaten bleiben getrennt vom DJI-Cloud-API-Ingress:

- `X-User-Token`
- `X-Project-Uuid`
- `X-Request-Id`
- `X-Language`

Der FH2-Adapter bleibt aktuell read-only.
