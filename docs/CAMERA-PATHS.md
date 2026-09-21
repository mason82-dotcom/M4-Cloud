# DJI Kamera- und Videopfade in M4-Cloud

## Ziel

M4 soll Kameraquellen nicht anhand fester Modellannahmen erraten. Die
verfügbaren Kamera- und Videopfade werden stattdessen dynamisch aus der
DJI-Cloud-API eingelesen.

Lyrebird ist für diesen Pfad nicht erforderlich und bleibt deaktiviert.

## Offizielle DJI-Quelle

Das offizielle DJI Cloud API Demo stellt die read-only Ressource bereit:

```http
GET /manage/api/v1/live/capacity
```

Die Anfrage wird mit dem von DJI verwendeten Header authentifiziert:

```http
x-auth-token: <access_token>
```

Der Access Token stammt im offiziellen Demo aus:

```http
POST /manage/api/v1/login
```

Die Login-Antwort enthält im offiziellen Modell außerdem:

```text
workspace_id
mqtt_username
mqtt_password
mqtt_addr
access_token
```

M4 automatisiert den Login in dieser Stufe noch nicht. Für die reine
Kameraerkennung wird der bereits vorhandene Access Token konfiguriert.

## M4-Konfiguration

```env
DJI_CLOUD_API_BASE_URL=https://cloud.example.local
DJI_CLOUD_API_TOKEN=...
DJI_CLOUD_API_VERIFY_TLS=true
DJI_CLOUD_API_TIMEOUT_SECONDS=15
```

Der Token wird nicht über Status-Endpunkte ausgegeben.

## Manager

Status:

```bash
./scripts/m4-manager.sh camera-status
```

Kamerapfade einlesen:

```bash
./scripts/m4-manager.sh camera-paths
```

Direkt per HTTP:

```bash
curl http://127.0.0.1:8080/api/v1/cameras/paths
```

## DJI Capacity-Datenmodell

Das offizielle Web-Demo verarbeitet folgende Struktur:

```text
device
  sn
  name
  cameras_list[]
    name
    index
    videos_list[]
      index
      type
      switch_video_types[]
```

Die Java-DTOs verwenden äquivalente CamelCase-Felder wie
`camerasList` und `videosList`. M4 akzeptiert beide Schreibweisen.

## Kameraindex / Payload Index

DJI beschreibt den Kamera-/Payload-Index als dreiteilige Kennung:

```text
type-subType-position
```

Beispiel:

```text
67-0-0
```

M4 behandelt diesen Wert als opaque DJI-Identifier. Es wird keine feste
Kamerazuordnung anhand einer selbst gepflegten Tabelle vorausgesetzt.

## Videotypen

Das DJI Cloud SDK definiert für Live-Capacity:

```text
zoom
wide
thermal
normal
ir
```

Für den Lens-Switch sind im offiziellen SDK explizit vorgesehen:

```text
zoom
wide
ir
```

M4 liest die tatsächlich vom Server gelieferten Werte ein und erzwingt keine
modellabhängige Vorauswahl.

## Video-ID

DJI setzt die Video-ID aus drei Segmenten zusammen:

```text
<drone_sn>/<payload_index>/<video_index>
```

Beispiel:

```text
1581ABC/67-0-0/normal-0
```

M4 liefert diesen vollständigen Wert als `video_id`.

## Fallback normal-0

Das offizielle DJI-Web-Demo verwendet bei einer Kamera ohne expliziten
Videoeintrag:

```text
normal-0
```

M4 übernimmt dieses Verhalten, markiert einen so erzeugten Eintrag aber
zusätzlich:

```json
"fallback_video_index": true
```

Damit kann später unterschieden werden, ob der Videopfad direkt von der API
kam oder gemäß dem DJI-Demo-Verhalten ergänzt wurde.

## Beispielantwort von M4

```json
{
  "source": "dji-cloud-api-live-capacity",
  "count": 1,
  "paths": [
    {
      "device_sn": "1581ABC",
      "device_name": "Mavic 3T",
      "camera_name": "Mavic 3T",
      "camera_index": "67-0-0",
      "video_index": "normal-0",
      "video_type": "normal",
      "switchable_video_types": ["wide", "zoom", "ir"],
      "video_id": "1581ABC/67-0-0/normal-0",
      "fallback_video_index": false
    }
  ]
}
```

Die Beispielwerte dienen ausschließlich der Darstellung. Im Betrieb kommen die
Pfade aus der konfigurierten API.

## Read-only-Sicherheitsgrenze

Die Kameraerkennung führt keine der folgenden Aktionen aus:

- Livestream starten
- Livestream stoppen
- Streamqualität ändern
- Linse umschalten
- Kamera-Modus ändern
- Foto auslösen
- Aufnahme starten/stoppen
- Payload Control übernehmen

Die offiziellen Cloud-API-Demo-Pfade für Start/Stop/Update/Switch sind bekannt,
werden aber in diesem M4-Schritt nicht exponiert.

## Multispektral

Multispektral verwendet künftig die dynamische Kameraliste als
Eingangsgrundlage. Dadurch kann die Verarbeitung anhand der real gemeldeten
Payload-/Videoquellen entscheiden, statt feste Kameranamen zu erwarten.

Media-Dateien besitzen im DJI-Cloud-SDK zusätzlich Aufnahme-Metadaten wie:

- absolute Höhe
- relative Höhe
- Aufnahmezeit
- Gimbal-Yaw
- Aufnahmeposition

Diese Media-Metadaten werden in einem separaten Schritt mit den erkannten
Kamerapfaden und Flugaufgaben verknüpft.

## RC Pro

RC Pro prüft im realen Betrieb insbesondere:

1. welche Kamerapfade `live/capacity` bei der eingesetzten Kombination
   tatsächlich meldet
2. wie sich die Liste bei Kamera-/Linsenwechsel verändert
3. welche `video_id` für den realen Livestream akzeptiert wird
4. ob ein Token-Refresh die Capacity-Abfrage beeinflusst

M4 selbst bleibt bei dieser Funktion read-only.


## Kamera-/Gimbal-Telemetrie

Zusätzlich zu den statischen Live-Capacity-Pfaden normalisiert M4 die zuletzt
persistierten DJI-MQTT-Ereignisse:

```http
GET /api/v1/cameras/telemetry
```

Manager:

```bash
./scripts/m4-manager.sh camera-telemetry
```

Der Endpoint ist read-only und dient als gemeinsame Grundlage für RC Pro und
Multispektral. Kamera- und Gimbal-Werte werden aus real eingehenden Events
abgeleitet; M4 sendet darüber keine Steuerkommandos.
