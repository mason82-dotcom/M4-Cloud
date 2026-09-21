# M4-Cloud Arbeitsmodell

## Ziel

M4-Cloud wird ab V1.1 nach einem klaren Manager-Modell weiterentwickelt.

Der **Manager** liefert neue Features in das Produkt. Die spezialisierten
Agenten **RC Pro** und **Multispektral** unterstützen ihn mit Fachwissen,
Implementierungsvorschlägen, Tests und Integrationsdaten.

Der maßgebliche Arbeits- und Zielbranch ist:

```text
main
```

Zusätzliche Feature-/Integrationsbranches werden nur noch angelegt, wenn dies
explizit angefordert wird.

## Rollen

### Manager

Der Manager ist Owner der Feature-Lieferung und der Integration.

Aufgaben:

- Feature-Backlog priorisieren
- Anforderungen in umsetzbare Arbeitspakete zerlegen
- Beiträge von RC Pro und Multispektral zusammenführen
- Backend, API, Deployment, Manager-Skripte und Dokumentation konsistent halten
- Änderungen gegen bestehende Funktionen regressionsprüfen
- CI und lokale Verifikationspfade pflegen
- neue Features direkt in `main` integrieren
- Versionierung und Changelog fortschreiben
- verhindern, dass parallele inkompatible Implementierungen entstehen

Der Manager entscheidet damit über den finalen technischen Stand von M4-Cloud.

### RC Pro

RC Pro ist der Spezialist für die DJI-Geräte- und Controller-Seite.

Schwerpunkte:

- DJI RC Pro Enterprise
- Mobile SDK / Controller-Anbindung
- Verbindung zwischen Controller, Drohne und M4
- Geräteinformationen und reale Laufzeitdaten
- HTTP-/Netzwerkverhalten auf dem Controller
- DJI Cloud-API-nahe Integrationspfade
- praktische Verifikation auf echter DJI-Hardware
- Rückmeldung an den Manager über notwendige API-/Backend-Anpassungen

RC Pro liefert seine Ergebnisse an den Manager. Der Manager übernimmt die
Produktintegration.

### Multispektral

Multispektral ist der Spezialist für Kamera-, Medien- und
Multispektral-Workflows.

Schwerpunkte:

- Kameraquellen und Payload-Daten
- multispektrale Aufnahmen
- Bild-/Medienmetadaten
- Mapping- und Verarbeitungsprofile
- NDVI-/Multispektral-relevante Datenpfade
- Medienübergabe an nachgelagerte Mapping-/Processing-Komponenten
- Prüfung, ob FH2-/DJI-Datenmodelle für die benötigten Sensorinformationen
  ausreichen
- Rückmeldung an den Manager über notwendige API-, Datenmodell- und
  Persistenzanpassungen

Multispektral liefert seine Ergebnisse ebenfalls an den Manager. Der Manager
übernimmt die Produktintegration.

## Zusammenarbeit

Der normale Featurefluss ist:

```text
                +----------------+
                |    RC Pro      |
                | DJI/Controller |
                +-------+--------+
                        |
                        v
+---------------+   +---+----------------+   +----------------------+
| Multispektral |-->|      Manager       |-->| M4-Cloud main        |
| Kamera/Media  |   | Integration/Tests  |   | ausgeliefertes       |
+---------------+   +--------------------+   | Feature              |
                                              +----------------------+
```

RC Pro und Multispektral können dasselbe Feature gemeinsam unterstützen.
Beispiel:

1. RC Pro bestätigt, welche Kameraquelle oder Geräteinformation tatsächlich
   auf Controller/Drohne verfügbar ist.
2. Multispektral definiert, wie diese Daten fachlich interpretiert und
   weiterverarbeitet werden.
3. Manager implementiert den stabilen M4-API-/Backend-/Deployment-Pfad.
4. Tests und Dokumentation werden gemeinsam gegen die reale Nutzung geprüft.
5. Der geprüfte Stand liegt in `main`.

## Regeln für main

`main` ist gleichzeitig Arbeits- und Lieferbranch des Managers.

Trotz direkter Entwicklung gelten weiterhin Qualitäts-Gates:

1. bestehende Tests dürfen nicht regressieren
2. neue Features erhalten Tests
3. Konfigurationsänderungen werden in `.env.example` dokumentiert
4. relevante API-Änderungen werden in `docs/API.md` dokumentiert
5. DJI-spezifische Änderungen werden in der passenden DJI-Dokumentation
   dokumentiert
6. Secrets werden niemals committed
7. physische/flugwirksame DJI-Funktionen erhalten eine explizite
   Sicherheitsklassifizierung
8. nach relevanten Laufzeitänderungen wird der reale
   `m4-manager.sh verify`-Pfad berücksichtigt

## Sicherheitsklassen für DJI-Funktionen

### READ

Nur lesend, beispielsweise:

- Geräte
- HMS
- Waylines lesen
- Flight Tasks lesen
- Status-/Telemetrieinformationen

Diese Funktionen können regulär durch den Manager integriert werden.

### WRITE

Verändert Daten, löst aber keine unmittelbare physische Flugaktion aus.

Beispiele:

- Metadaten ändern
- Wayline hochladen
- Konfiguration speichern

WRITE-Funktionen werden separat implementiert und getestet.

### DANGEROUS

Kann reale Hardware bewegen, Flugbetrieb beeinflussen, Daten löschen oder
Quota/Kosten auslösen.

Beispiele:

- Mission starten
- RTH
- Aircraft Control
- Payload Control
- destruktive Operationen
- kosten-/quota-relevante Rekonstruktion

DANGEROUS-Funktionen werden niemals implizit freigeschaltet und benötigen eine
eigene Schutz- und Freigabelogik.

## Temporär deaktivierte Integrationspfade

### Lyrebird

Lyrebird ist bis auf Weiteres **deaktiviert** und wird nicht als Bestandteil
des aktuellen M4-Integrationspfads verwendet.

Das bedeutet:

- keine neue M4-Funktion darf Lyrebird voraussetzen
- RC Pro verwendet für neue M4-Arbeit primär offizielle DJI-Schnittstellen,
  dokumentierte Cloud-API-/Mobile-SDK-Pfade und direkte Hardwareverifikation
- Multispektral baut keine Kamera-/Media-Pipeline auf Lyrebird auf
- der Manager integriert keine Lyrebird-spezifischen Abhängigkeiten in `main`
- vorhandene externe Lyrebird-Arbeit bleibt davon unberührt und wird nicht
  automatisch gelöscht

Eine Reaktivierung erfolgt nur auf ausdrückliche Anweisung.

## Verantwortung bei Konflikten

Wenn RC Pro und Multispektral unterschiedliche technische Anforderungen
melden, entscheidet der Manager anhand von:

- offizieller DJI-Dokumentation
- Verhalten der realen Hardware
- bestehender M4-Architektur
- Rückwärtskompatibilität
- Sicherheitsauswirkungen
- Testbarkeit

Eine neue Parallelarchitektur wird nur eingeführt, wenn der bestehende M4-Pfad
die Anforderung nachweislich nicht sauber abbilden kann.

## Dokumentationspflicht

Jedes neue Feature muss so dokumentiert sein, dass es später ohne Kenntnis der
ursprünglichen Chat-Unterhaltung betrieben und weiterentwickelt werden kann.

Dazu gehören je nach Feature:

- Installation
- Konfiguration
- Manager-Kommandos
- API
- Fehlersuche
- Sicherheitsgrenzen
- reale Testschritte
