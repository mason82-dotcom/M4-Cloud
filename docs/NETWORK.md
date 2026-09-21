# Netzwerk und Ports

## Standardports

| Port | Richtung | Zweck | Default-Bind |
| --- | --- | --- | --- |
| 8080/TCP | LAN -> M4 | HTTP/API/Health | 0.0.0.0 |
| 1883/TCP | Gerät/Adapter -> MQTT | MQTT Bootstrap | 127.0.0.1 |
| 5432/TCP | intern | PostgreSQL | nicht veröffentlicht |
| 8000/TCP | intern | Control API | nicht veröffentlicht |

## Sicherheitsvorgaben

- PostgreSQL wird nicht auf den Host veröffentlicht.
- Die Control API ist ausschließlich über den Reverse Proxy erreichbar.
- MQTT ist im Bootstrap nur an Host-Loopback gebunden.
- Vor MQTT-LAN-Freigabe müssen Authentifizierung und TLS konfiguriert werden.
- Keine Secrets im Git-Repository.
- Externe FH2-Endpunkte werden nur über `FH2_UPSTREAM_BASE_URL` konfiguriert.
- Für produktive Bereitstellung TLS am Reverse Proxy terminieren.

## LAN-Freigabe

HTTP ist für das Heim-/LAN-Netz vorbereitet. MQTT bleibt absichtlich lokal,
bis die abgesicherte DJI-Integrationskonfiguration feststeht.
