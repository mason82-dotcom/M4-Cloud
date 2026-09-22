# DRC-Design-Gate

DRC ist in M4 weiterhin **deaktiviert**. Dieses Dokument hält die verifizierte
DJI-Topic- und Sequenzsemantik fest.

## 1. Topic-Richtung

```text
thing/product/{gateway_sn}/drc/down
Cloud -> Gerät

thing/product/{gateway_sn}/drc/up
Gerät -> Cloud
```

Steuerbefehle dürfen daher niemals auf `drc/up` publiziert werden.

## 2. DRC-Modus

Der DRC-Link wird über das normale Service-Topic aufgebaut:

```text
thing/product/{gateway_sn}/services
method: drc_mode_enter
```

Die Antwort kommt über:

```text
thing/product/{gateway_sn}/services_reply
method: drc_mode_enter
```

DJI erwartet dabei unter anderem einen dedizierten MQTT-Broker-Datensatz mit
`address`, `client_id`, `username`, `password`, `expire_time`,
`enable_tls`, `osd_frequency` und `hsi_frequency`.

## 3. Aktuelle Stick-Steuerung

Für aktuelle RC-Pro-/Dock-DRC-Pfade ist `stick_control` der bevorzugte
Befehl:

```text
Topic:  thing/product/{gateway_sn}/drc/down
Method: stick_control
Rate:   5-10 Hz
ACK:    keiner
```

Beispielstruktur:

```json
{
  "seq": 1,
  "method": "stick_control",
  "data": {
    "roll": 1024,
    "pitch": 1024,
    "throttle": 1024,
    "yaw": 1024
  }
}
```

Neutralwert ist 1024. Der dokumentierte Kanalbereich ist 1024 ± 660.

## 4. Legacy drone_control

Das ältere `drone_control` verwendet:

```text
Topic: thing/product/{gateway_sn}/drc/down
```

und die Sequenznummer liegt innerhalb von `data`:

```json
{
  "method": "drone_control",
  "data": {
    "seq": 1,
    "x": 0,
    "y": 0,
    "h": 0,
    "w": 0
  }
}
```

DJI dokumentiert, dass die Sequenz bei einer Änderung der Werte `x/y/h/w`
wieder bei 0 beginnen soll. Für neuere Dock-2-Dokumentation ist dieser Befehl
als veraltet markiert.

## 5. Heartbeat

```text
Topic:  thing/product/{gateway_sn}/drc/down
Method: heart_beat
```

Bei den aktuellen Protokollen liegt `seq` auf derselben Ebene wie `data`.
Bleibt der Heartbeat länger als etwa eine Minute aus, kann das Gerät den
DRC-Link als idle betrachten und verlassen.

M4 behandelt später getrennt:

- Heartbeat-Sequenz
- Stick-Control-Sequenz
- Legacy-drone_control-Sequenz

## 6. Emergency Stop

```text
Topic:  thing/product/{gateway_sn}/drc/down
Method: drone_emergency_stop
```

Antwort:

```text
thing/product/{gateway_sn}/drc/up
method: drone_emergency_stop
```

Die genaue Payload-/Seq-Form ist geräte- und Protokollversionsabhängig. M4
darf deshalb nicht eine einzige Payloadform für alle RC-/Dock-Generationen
hart kodieren.

Der Fehlercode `319031` ist aktuell allgemein als Flight-Control-Fehler
dokumentiert. Eine feste 2-Sekunden-Cooldown-Regel wird nicht allein aus
diesem Fehlercode abgeleitet.

## 7. FlyTo

`fly_to_point` läuft über:

```text
thing/product/{gateway_sn}/services
```

Fortschritt:

```text
thing/product/{gateway_sn}/events
method: fly_to_point_progress
```

`commander_flight_height` besitzt laut Schema einen Minimalwert von 2 m.
Zusätzlich beschreibt DJI eine Sicherheitslogik, nach der ein Fluggerät unter
20 m relativer Höhe zunächst auf 20 m steigen kann. Schema-Minimum und
operative Sicherheitslogik werden deshalb getrennt behandelt.

## 8. OSD während DRC

Aktuelle DRC-Protokolle können hochfrequente Telemetrie über:

```text
thing/product/{gateway_sn}/drc/up
method: osd_info_push
```

liefern.

Dieser Pfad ist in M4 derzeit absichtlich nicht freigegeben. Der neue
`/ws/v1/telemetry`-Pfad nutzt zunächst normale DJI-`osd/state/events/status`
Topics. Eine garantierte Sub-Sekunden-End-to-End-Latenz kann daraus nicht
abgeleitet werden; sie hängt von der DJI-Quellfrequenz ab.

## 9. ACL-Architektur

### Aktuelle Runtime: Mosquitto

M4 V2.0 verwendet Mosquitto. DRC-Topics bleiben dort vollständig gesperrt.

Die WebUI verbindet sich **nicht direkt mit MQTT**. Sie erhält Telemetrie über
den M4-WebSocket. Dadurch benötigt der Browser keine MQTT-Credentials und
keine Broker-Publish-Rechte.

### Späterer dedizierter DRC-Broker: EMQX

Wenn für DRC ein separater EMQX-Broker eingesetzt wird:

- `authorization.no_match = deny`
- Abschlussregel `{deny, all}.`
- keine Wildcards in Client-ID/Username
- `${clientid}` und `${username}` kontrolliert als Topic-Platzhalter
- keine Client-Matcher-Regel wie `{clientid, "${clientid}"}`
- kurzlebige DRC-Credentials
- TLS
- getrennte Rollen für Telemetrie und Steuerung

Beispielprinzip, **nicht aktive M4-Konfiguration**:

```erlang
{allow, {username, "drc-backend"}, subscribe,
 ["thing/product/+/drc/up"]}.

{allow, {username, "drc-backend"}, publish,
 ["thing/product/+/drc/down"]}.

{deny, all}.
```

Die Produktions-ACL muss zusätzlich Gateway-/Session-Bindung erzwingen.

## 10. Freigabereihenfolge

DRC wird erst implementiert, wenn diese Gates erfüllt sind:

1. read-only OSD-/State-WebSocket stabil
2. WSS/WebUI-Session-Authentifizierung
3. dedizierter DRC-MQTT-TLS-Pfad
4. kurzlebige Credentials
5. Gateway-/Session-spezifische ACL
6. Flight-Authority-State-Machine
7. Heartbeat-/Timeout-State-Machine
8. Simulation/Mock-Tests
9. explizite Director-Freigabe
10. erst dann echte Steuerbefehle

Bis dahin bleibt `drc_enabled=false`.
