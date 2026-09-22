# RC Pro Gateway Discovery

## Ziel

DJI RC Pro Enterprise / Pilot 2 wird als Gateway behandelt. Die Zuordnung
zwischen Gateway und Aircraft entsteht aus `update_topo`.

## Verifizierter Topology-Pfad

DJI dokumentiert `update_topo` mit `gateway_sn` und einer
`sub_devices`-Liste. Die allgemeine Topic-Definition verwendet:

```text
sys/product/{gateway_sn}/status
```

Die RC-Pro-spezifische Device-Referenz zeigt zusätzlich:

```text
thing/product/{gateway_sn}/status
```

M4 akzeptiert deshalb beide Varianten **read-only**, bis die reale RC-Pro-
Firmware den tatsächlich verwendeten Pfad bestätigt.

## Registry

Beim Event:

```json
{
  "method": "update_topo",
  "data": {
    "type": 119,
    "sub_devices": [
      {
        "sn": "M3E-001",
        "type": 60,
        "index": "A"
      }
    ]
  }
}
```

registriert M4:

```text
M3E-001 -> RC-PRO-001
```

Öffentliche Abfrage:

```http
GET /api/v1/devices/topology
```

## Secret-Schutz

Das originale DJI-Topology-Event kann enthalten:

- `device_secret`
- `nonce`

für Gateway und Sub-Devices.

Diese Werte werden **nicht** in der öffentlichen Registry gespeichert und
**nicht** über `/ws/v1/telemetry` an die WebUI weitergereicht.

Der WebSocket erhält stattdessen ein Event:

```json
{
  "type": "dji.topology",
  "device_sn": "RC-PRO-001",
  "payload": {
    "method": "update_topo",
    "data": {
      "gateway": {
        "sn": "RC-PRO-001",
        "type": 119
      },
      "sub_devices": [
        {
          "sn": "M3E-001",
          "gateway_sn": "RC-PRO-001",
          "type": 60,
          "index": "A"
        }
      ]
    }
  }
}
```

## OSD-/State-Zuordnung

OSD und State sind nicht pauschal auf die Gateway-SN umzuschreiben. DJI
definiert die Topicform als:

```text
thing/product/{device_sn}/osd
thing/product/{device_sn}/state
```

Für Aircraft-Telemetrie kann `device_sn` deshalb die Drohnen-SN sein.
M4 nutzt die Registry, um diese Device-SN anschließend dem RC-Pro-Gateway
zuzuordnen.

## DRC

Die Discovery aktiviert kein DRC. Für spätere Commands wird die Registry
genutzt, um aus einer ausgewählten Aircraft-SN die zugehörige Gateway-SN zu
ermitteln. Erst danach darf ein eigener DRC-Service den Gateway-spezifischen
Downlink bestimmen.

Die korrekte DRC-Richtung bleibt:

```text
drc/down  Cloud -> RC Pro / Gerät
drc/up    RC Pro / Gerät -> Cloud
```

## Firmware-Hinweis

Die häufig genannten Mindeststände

```text
M3E/M3T/M3M             06.01.06.06
DJI RC Pro Enterprise   02.00.04.07
DJI Pilot 2             6.1.2.2
```

stammen aus älteren Cloud-API-Releases und waren dort gültige Mindeststände.
Neuere DJI-Cloud-API-Releases nennen bereits deutlich höhere Mindeststände.
M4 behandelt Firmwareanforderungen daher versionsgebunden und nicht als
zeitlos feste Konstanten.
