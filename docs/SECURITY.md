# Sicherheit V2.0

- zentrale CI ausschließlich durch den Direktor via `workflow_dispatch`
- Mosquitto: `allow_anonymous false`
- getrennte Credentials für M4-Service und DJI-/RC-Client
- DRC nicht freigegeben
- interner M4-Service besitzt im read-only Stand keine DJI-Command-Schreibrechte

## Bootstrap

`GET /api/v1/cloud/bootstrap` verlangt `X-M4-Bootstrap-Token`.
Ohne serverseitigen Token: HTTP 503. Falscher/fehlender Header: HTTP 401.
Das DJI-MQTT-Passwort wird nur nach erfolgreicher Bootstrap-Authentifizierung
ausgegeben.

## TLS-Grenze

MQTT 1883 ist authentifiziert, aber noch nicht TLS-verschlüsselt. Keine
Internetfreigabe; nur vertrauenswürdiges LAN/VLAN. Nächster Schritt ist ein
separater externer MQTT-TLS-Listener.
