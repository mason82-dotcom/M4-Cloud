# Netzwerk und Ports

## Standardports

| Port | Richtung | Zweck | Default-Bind |
| --- | --- | --- | --- |
| 8080/TCP | LAN -> M4 | HTTP/API/WebSocket/Health | 0.0.0.0 |
| 1883/TCP | Host -> MQTT | MQTT Bootstrap | 127.0.0.1 |
| 9090/TCP | Host -> Prometheus | optionales Monitoring | 127.0.0.1 |
| 5432/TCP | intern | PostgreSQL | nicht veröffentlicht |
| 8000/TCP | intern | Control API | nicht veröffentlicht |

`integration-worker` besitzt keinen Host-Port. Er konsumiert MQTT und schreibt
in PostgreSQL.

## Sicherheitsvorgaben

- PostgreSQL und Control API werden nicht auf den Host veröffentlicht.
- MQTT ist im Bootstrap nur an Host-Loopback gebunden.
- Prometheus ist nur an Host-Loopback gebunden.
- Vor MQTT-LAN-Freigabe müssen Authentifizierung und TLS konfiguriert werden.
- Keine Secrets im Git-Repository.
- Externe FH2-Endpunkte werden ausschließlich über Umgebungsvariablen konfiguriert.
- TLS-Verifikation zum FH2-Upstream ist standardmäßig aktiv.
- Für eine Veröffentlichung außerhalb eines kontrollierten LANs muss TLS und
  Authentifizierung am Reverse Proxy vorgeschaltet werden.

## DJI-Geräte / FH2

DJI Pilot 2, DJI Dock oder ein offizieller FH2-Server dürfen nur auf Ports
zugreifen, die für die tatsächlich verwendete offizielle Integrationsmethode
benötigt werden. M4 öffnet keine angenommenen proprietären DJI-Ports.
