# DJI FlightHub 2 und DJI Cloud API Integration

## Zwei getrennte DJI-Schnittstellen

M4-Cloud unterstützt zwei voneinander getrennte Integrationsrichtungen:

1. **FlightHub 2 / SkyKit OpenAPI**: M4 greift per HTTPS auf einen vorhandenen
   DJI-FlightHub-2-/SkyKit-Server zu.
2. **DJI Cloud API**: DJI Pilot 2 oder ein DJI Dock verbindet sich direkt mit
   der eigenen Cloud-Plattform. DJI beschreibt dafür insbesondere MQTT, HTTPS
   und WebSocket.

Die beiden Pfade ersetzen sich nicht und dürfen technisch nicht vermischt
werden.

## FlightHub 2 OpenAPI

Setzen:

```env
FH2_UPSTREAM_BASE_URL=https://fh2.example.local
FH2_API_TOKEN=...
FH2_UPSTREAM_VERIFY_TLS=true
```

`GET /api/v1/fh2/status` prüft die grundsätzliche Erreichbarkeit, ohne URL
oder Token in der API-Antwort preiszugeben.

M4 nimmt keine undokumentierten OpenAPI-Pfade an. Für aktuelle
FlightHub-2-/SkyKit-OpenAPI-Versionen werden die von DJI veröffentlichten
Endpunkte und Authentifizierungsheader gezielt im Adapter umgesetzt.

## DJI Cloud API

DJI Cloud API verbindet DJI Pilot 2 bzw. unterstützte Dock-/Enterprise-Geräte
direkt mit einer eigenen Cloud-Plattform. Der Transport basiert auf
Standardprotokollen wie MQTT, HTTPS und WebSocket.

### Phase 1 in M4: MQTT-Ingest

Aktivierung:

```env
DJI_CLOUD_API_ENABLED=true
```

Standardmäßig abonnierte DJI-Uplink-Topics:

```text
thing/product/+/osd
thing/product/+/state
thing/product/+/services_reply
thing/product/+/events
thing/product/+/requests
thing/product/+/property/set_reply
thing/product/+/drc/up
sys/product/+/status
```

Sie können über `DJI_CLOUD_API_TOPICS` überschrieben werden.

Empfangene Nachrichten werden unverändert in der bestehenden
`integration_events`-Persistenz gespeichert. DJI-Cloud-API-Topics erhalten
als Quelle `dji-cloud-api`; sonstige MQTT-Nachrichten bleiben `mqtt`.

Status:

```text
GET /api/v1/dji/cloud/status
```

Der Endpoint zeigt nur nicht-sensitive Laufzeitinformationen.

### Sicherheitsgrenze von Phase 1

Der aktuelle MQTT-Port bleibt standardmäßig nur an Host-Loopback gebunden:

```env
M4_MQTT_BIND=127.0.0.1
```

Das ist beabsichtigt. Pilot 2 oder ein externes DJI-Gerät kann damit noch
nicht direkt aus dem LAN auf den Broker zugreifen.

Vor einer LAN-Freigabe werden in einer eigenen Phase umgesetzt:

- MQTT-Benutzer/Passwort statt anonymem Zugriff,
- ACLs für DJI-Topics,
- TLS für MQTT,
- definierte externe Broker-Adresse,
- Pilot-2-Webview-/JSBridge-Bootstrap,
- App-ID/App-Key/License-Verifikation,
- Workspace-ID und Plattforminformationen.

Erst danach wird der Broker für Pilot 2 oder DJI Dock erreichbar gemacht.

### Downlink und Gerätesteuerung

Phase 1 verarbeitet nur Uplink/Telemetrie. DJI-Service-Downlinks,
Property-Set, Remote Flight Controls/DRC und andere Steuerbefehle werden noch
nicht von M4 erzeugt.

Das verhindert, dass vor abgeschlossener Authentifizierung und
Berechtigungsprüfung versehentlich Gerätebefehle gesendet werden.

## Offizielles DJI Cloud API Demo

Das frühere `DJI-Cloud-API-Demo` dient nur als Referenz zum Verständnis des
Protokollflusses. DJI hat die Wartung dieses Demo-Projekts am 10. April 2025
eingestellt und weist darauf hin, dass es keine produktionsreife Lösung ist.

M4 kopiert daher nicht den alten Java/MySQL/Redis/EMQX-Demo-Stack, sondern
implementiert die benötigten DJI-Protokollgrenzen in der bestehenden
FastAPI/PostgreSQL/Podman-Architektur.

## Nächste Ausbauphase

Nach erfolgreicher Phase-1-Abnahme folgen:

1. MQTT Auth + ACL + TLS.
2. Pilot-2-Cloud-Services-Einstiegsseite.
3. JSBridge License Verify und Cloud Module Bootstrap.
4. Workspace-/Platform-Konfiguration.
5. Topology-/Status-Verarbeitung.
6. definierte Service-Replies und Requests-Replies.
7. anschließend ausgewählte, explizit freigegebene Downlink-Kommandos.


## Pilot 2 Bootstrap API

M4 stellt einen eigenen, token-geschützten Bootstrap-Endpunkt bereit:

```text
GET /api/v1/dji/cloud/bootstrap
X-M4-Bootstrap-Token: <DJI_BOOTSTRAP_TOKEN>
```

Der Endpoint ist **kein DJI-Endpunkt**. Er liefert der M4-H5-WebView die Werte,
die anschließend über die DJI JSBridge an Pilot 2 übergeben werden:

- Platform-/Workspace-Informationen,
- DJI App ID / App Key / License,
- API Host + X-Auth-Token,
- WebSocket Host + Token,
- MQTT Host + Username + Passwort,
- freigegebene M4-Funktionen.

Solange `DJI_CLOUD_API_ENABLED=false` ist oder Pflichtwerte fehlen, liefert
der Endpoint keine Bootstrap-Konfiguration.

Die DJI Developer Credentials werden nicht im Repository gespeichert. Sie
werden ausschließlich über `.env` bzw. die installierte Runtime-Umgebung
bereitgestellt.

## MQTT Authentifizierung und ACL

Der M4-Broker akzeptiert keine anonymen MQTT-Clients mehr.

Interne Rollen:

- `m4-worker`: ausschließlich Lesen der M4-/DJI-Uplink-Topics.
- `m4-health`: Healthcheck sowie definierte Verify-/CI-Testpublishes.
- `dji-pilot`: nur bei aktivierter DJI Cloud API.

Die `dji-pilot`-ACL erlaubt Schreiben nur auf die DJI-Uplink-Richtung:

```text
thing/product/+/osd
thing/product/+/state
thing/product/+/services_reply
thing/product/+/events
thing/product/+/requests
thing/product/+/property/set_reply
sys/product/+/status
```

Lesen ist nur für die DJI-Cloud-Downlink-Antwortkanäle vorgesehen:

```text
thing/product/+/services
thing/product/+/events_reply
thing/product/+/requests_reply
thing/product/+/property/set
sys/product/+/status_reply
```

`drc/up` und `drc/down` sind für `dji-pilot` in dieser Phase nicht
freigegeben.

Der Broker bleibt weiterhin standardmäßig nur auf
`127.0.0.1:1883` am Host veröffentlicht. Username/Passwort ohne TLS dürfen
nicht als LAN-/WAN-Produktionszugang verwendet werden. Der nächste Schritt ist
ein separater TLS-Listener für Pilot 2.
