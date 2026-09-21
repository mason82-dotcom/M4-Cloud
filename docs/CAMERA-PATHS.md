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

## Kamera-/Gimbal-Telemetrie

Zusätzlich zu den statischeren Live-Capacity-Pfaden kann M4 den zuletzt
persistierten DJI-MQTT-Zustand normalisieren:

```http
GET /api/v1/cameras/telemetry?limit=200
```

Manager:

```bash
./scripts/m4-manager.sh camera-telemetry
./scripts/m4-manager.sh camera-telemetry 500
```

Der Normalizer arbeitet ausschließlich auf bereits empfangenen und
persistierten MQTT-Ereignissen. Für reale DJI-Telemetrie müssen die in der
Zielinstallation freigegebenen Topics über `DJI_MQTT_TOPICS` abonniert sein.
Der sichere Default `m4/fh2/#` wird dadurch nicht automatisch erweitert.

### DJI Kamera-State

Für `thing/product/<sn>/osd` und `thing/product/<sn>/state` liest M4 aus
`data.cameras[]` unter anderem die tatsächlich vorhandenen Felder:

```text
payload_index
camera_mode
photo_state
recording_state
screen_split_enable
remain_photo_num
remain_record_duration
record_time
zoom_factor
ir_zoom_factor
photo_storage_settings
video_storage_settings
wide_exposure_mode
wide_iso
wide_shutter_speed
wide_exposure_value
zoom_exposure_mode
zoom_iso
zoom_shutter_speed
zoom_exposure_value
zoom_focus_mode
zoom_focus_value
zoom_max_focus_value
zoom_min_focus_value
zoom_calibrate_farthest_focus_value
zoom_calibrate_nearest_focus_value
zoom_focus_state
ir_metering_mode
ir_metering_point
ir_metering_area
```

Nicht vorhandene Felder werden nicht erfunden und nicht mit Defaultwerten
gefüllt.

### Gimbal

M4 normalisiert folgende Winkel, wenn sie vom DJI-Datenpfad geliefert werden:

```text
gimbal_pitch
gimbal_roll
gimbal_yaw
```

Die Zuordnung erfolgt ausschließlich über den von DJI gelieferten
`payload_index` oder über einen Payload-Key im Format
`<type>-<subType>-<position>`.

Wenn ein Gimbal-Datensatz keine eindeutige Payload-Kennung enthält, bleibt:

```json
"payload_index": null
```

M4 ordnet ihn nicht heuristisch einer Kamera zu.

Bereits persistierte High-Frequency-/DRC-Telemetrie kann vom Parser gelesen
werden. Der Telemetrie-Endpunkt aktiviert jedoch weder DRC noch Payload Control
und sendet keine Kamera- oder Gimbalbefehle.

### Snapshot-Zusammenführung

`recent_events()` liefert die Ereignisse newest-first. Der Telemetrieparser
behält daher den neuesten Wert eines Feldes und ergänzt nur Felder, die im
neueren Partial-Update fehlen. Dadurch bleiben etwa ein neuer Gimbalwinkel und
der zuletzt bekannte Kamera-/Zoomzustand gemeinsam sichtbar, ohne ältere Werte
über neuere zu schreiben.

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
