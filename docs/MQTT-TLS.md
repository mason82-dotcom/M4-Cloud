# MQTT-TLS für DJI Pilot 2 / Dock

## Status

Dieser Baustein ist ein optionaler Follow-up für den Direktor. Er ist
standardmäßig deaktiviert und verändert den internen MQTT-Pfad auf Port 1883
nicht.

Aktiviert wird TLS ausschließlich über:

```text
docker-compose.tls.yml
```

Der externe Listener verwendet Port `8883`.

## Sicherheitsmodell

```text
M4 intern -> mqtt:1883

DJI Pilot 2 / Dock
        |
        | MQTT + TLS
        v
M4 Host :8883
        |
        v
Mosquitto
        +-- Username/Password
        +-- bestehende ACL
        +-- DRC weiterhin gesperrt
```

Der TLS-Listener nutzt mindestens TLS 1.2 und `require_certificate false`.
Damit authentifiziert der Client den Server; MQTT-Username/Passwort bleiben
für die Broker-Authentifizierung aktiv. Client-Zertifikate werden in dieser
Stufe nicht verlangt.

## Zertifikate

Zertifikat und Private Key liegen nicht im Repository.

Standardpfade:

```text
./secrets/mqtt-tls/server.crt
./secrets/mqtt-tls/server.key
```

`secrets/` ist git-ignored.

Für einen realen Pilot-2-Test muss das Zertifikat zum DNS-Namen in
`MQTT_PUBLIC_HOST` passen und eine vollständige vertrauenswürdige Chain
liefern. Die DJI-Dokumentation nennt GoDaddy-Zertifikate ausdrücklich als
Unterstützungsweg für MQTT SSL.

## Konfiguration

```env
MQTT_PUBLIC_HOST=m4.example
MQTT_TLS_BIND=0.0.0.0
MQTT_TLS_PORT=8883
MQTT_TLS_CERT_FILE=./secrets/mqtt-tls/server.crt
MQTT_TLS_KEY_FILE=./secrets/mqtt-tls/server.key
DJI_CLOUD_API_ENABLED=true
```

Der Basiswert `MQTT_BIND=127.0.0.1` bleibt unverändert.

## Statische Prüfung

```bash
./scripts/verify-tls-config.sh
```

Der Prüfer kontrolliert Zertifikat/Key, Hostnamen und das Compose-Overlay,
startet aber keinen Container.

## Kontrollierter Start

```bash
docker compose \
  -f docker-compose.yml \
  -f docker-compose.tls.yml \
  up -d --build
```

Danach:

```bash
curl -s http://127.0.0.1:8080/api/v1/system | jq
curl -s http://127.0.0.1:8080/api/v1/cloud/bootstrap | jq
```

Der Bootstrap soll `mqtt.tls=true` und Port 8883 melden, aber weiterhin kein
MQTT-Passwort ausgeben.

## TLS-Handschlag

```bash
openssl s_client \
  -connect m4.example:8883 \
  -servername m4.example \
  -verify_hostname m4.example \
  -verify_return_error </dev/null
```

## Noch offen

- realer RC-Pro-Enterprise-/Pilot-2-Test
- unterstützte MQTT-URI-/JSBridge-Parameter der installierten Pilot-2-Version
- H5-/JSBridge-Login und License Verify
- sichere Session-/Credential-Ausgabe
- WebSocket-/HTTPS-TLS
- dynamische gerätebezogene ACLs
- DRC bleibt separat und deaktiviert
