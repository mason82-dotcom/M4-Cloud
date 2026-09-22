# Sicherheit V2.0

## CI-Verantwortung

Die zentrale GitHub-Actions-Validation wird ausschließlich vom **Direktor**
manuell über `workflow_dispatch` gestartet und bewertet. Manager, RC Pro und
Multispektral liefern Code, lokale Prüfschritte und Dokumentation, starten aber
keine CI.

## MQTT

Mosquitto läuft mit:

- `allow_anonymous false`
- getrennten Credentials für `m4-service` und `dji-client`
- dynamisch erzeugter ACL
- DRC explizit nicht freigegeben

Der M4-Service besitzt im aktuellen read-only Stand keine Berechtigung,
`thing/product/+/services` oder `thing/product/+/property/set` zu
publizieren. Gerätekommandos werden erst mit einer separaten Write-Freigabe
eingeführt.

Der DJI-/RC-Client darf die dokumentierten Status-/State-/OSD-/Event-/Request-
und Reply-Uplinks publizieren und die vorgesehenen Downlink-Topics abonnieren.

## Bootstrap

`GET /api/v1/cloud/bootstrap` verlangt:

```text
X-M4-Bootstrap-Token: <DJI_BOOTSTRAP_TOKEN>
```

Ohne serverseitig konfigurierten Token liefert M4 HTTP 503. Ein falscher oder
fehlender Header liefert HTTP 401. Das MQTT-Passwort wird nur nach erfolgreicher
Bootstrap-Authentifizierung zurückgegeben.

`DJI_BOOTSTRAP_TOKEN` gehört ausschließlich in `.env` bzw. eine sichere
Secret-Verwaltung und niemals ins Repository.

## LAN und TLS

V2.0 kann MQTT für RC Pro im vertrauenswürdigen LAN bereitstellen. Der aktuelle
Brokerlistener ist jedoch noch **nicht TLS-verschlüsselt**. Deshalb gilt:

- keine Internetfreigabe von Port 1883
- nur vertrauenswürdiges LAN/VLAN
- starke, individuelle MQTT-Passwörter
- Firewall auf benötigte Netze begrenzen
- vor WAN oder nicht vertrauenswürdigen Netzen MQTT-TLS bzw. einen gesicherten
  Tunnel einsetzen

Der nächste Security-Ausbauschritt ist ein separater externer TLS-Listener,
ohne den internen Brokerpfad unnötig zu öffnen.

## FlightHub 2

FH2 bleibt ein separater read-only Adapter. `FH2_USER_TOKEN` wird nicht in
Statusantworten ausgegeben. Schreibende oder flugwirksame Operationen bleiben
außerhalb von V2.0.
