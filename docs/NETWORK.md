# Netzwerk und Ports

| Port | Richtung | Zweck | Default |
| --- | --- | --- | --- |
| 8080/TCP | LAN -> M4 | HTTP/API/WebSocket | `0.0.0.0` |
| 1883/TCP | Host -> MQTT | authentifiziertes internes MQTT | `127.0.0.1` |
| 9090/TCP | Host -> Prometheus | Monitoring | `127.0.0.1` |
| 5432/TCP | intern | PostgreSQL | nicht veröffentlicht |
| 8000/TCP | intern | Control API | nicht veröffentlicht |

## MQTT

Aktuell:

- Anonymous deaktiviert
- Passwortauthentifizierung aktiv
- ACL aktiv
- Host-Bind nur Loopback
- kein externer TLS-Listener

Damit kann Pilot 2 derzeit nicht direkt über LAN produktiv auf den Broker zugreifen. Das ist beabsichtigt.

## HTTP

Port 8080 ist aktuell HTTP. Für reale Pilot-2-H5-/Bootstrap-Nutzung ist HTTPS erforderlich.

## FlightHub 2

FH2 wird ausgehend per HTTPS angesprochen. Es werden keine proprietären DJI-Ports angenommen oder geöffnet.

## Firewall

Nur explizit benötigte Ports freigeben. Vor VLAN-/Internet-Freigabe: TLS, Authentifizierung, Quellnetzbegrenzung und Credential-Rotation.
