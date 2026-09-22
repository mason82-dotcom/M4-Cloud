# Sicherheit V2.0

## CI-Verantwortung

Die zentrale GitHub-Actions-Validation wird ausschließlich vom **Direktor**
manuell über `workflow_dispatch` gestartet und bewertet. Manager, RC Pro und
Multispektral starten keine CI.

## MQTT

Mosquitto nutzt:

- `allow_anonymous false`
- getrennte Credentials für `m4-service` und `dji-client`
- ACLs pro Rolle
- keine DRC-Freigabe

Der interne M4-Service darf im aktuellen V2.0-Read-only-Stand keine
`services`- oder `property/set`-Kommandos publizieren. Diese Rechte werden
erst mit einer separaten Write-Freigabe eingeführt.

## Bootstrap

`GET /api/v1/cloud/bootstrap` verlangt:

```text
X-M4-Bootstrap-Token: <DJI_BOOTSTRAP_TOKEN>
```

Ohne serverseitig konfigurierten Token liefert M4 HTTP 503. Ein falscher oder
fehlender Header liefert HTTP 401. Das DJI-MQTT-Passwort wird nur nach
erfolgreicher Bootstrap-Authentifizierung zurückgegeben.

`DJI_BOOTSTRAP_TOKEN` gehört ausschließlich in `.env` bzw. eine sichere
Secret-Verwaltung und niemals ins Repository.

## LAN und TLS

Der aktuelle MQTT-Listener ist authentifiziert, aber noch nicht
TLS-verschlüsselt. Deshalb gilt:

- Port 1883 nicht ins Internet veröffentlichen
- nur vertrauenswürdiges LAN/VLAN verwenden
- starke individuelle Passwörter setzen
- Firewall auf benötigte Netze begrenzen
- für WAN/nicht vertrauenswürdige Netze MQTT-TLS oder einen sicheren Tunnel
  einsetzen

Nächster Security-Ausbauschritt: separater externer TLS-Listener für DJI/RC.

## FlightHub 2

FH2 bleibt ein separater read-only Adapter. `FH2_USER_TOKEN` wird nicht in
Statusantworten ausgegeben. Schreibende oder flugwirksame Operationen bleiben
außerhalb von V2.0.
