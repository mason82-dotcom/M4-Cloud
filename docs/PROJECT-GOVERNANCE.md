# Projektsteuerung

## Branch

Der kanonische Entwicklungs- und Zielbranch ist `main`.

## Rollen

- **Direktor**: Architektur, Integrationsgrenzen, CI, Freigabe und Gesamtkoordination.
- **Manager**: Featureplanung und Umsetzung innerhalb der gesetzten Architektur.
- **RC Pro**: RC-/MSDK-nahe Beiträge.
- **Multispektral**: Kamera-, Payload- und Multispektral-Mappings.

Nur der Direktor verändert CI-Konfiguration, startet CI-Läufe und bewertet deren Ergebnis. Manager, RC Pro und Multispektral liefern ausschließlich Code, lokale Tests und Prüfanweisungen zu.

## Ausgeschlossen

- M3-Cloud als Abhängigkeit
- Lyrebird als aktiver Bestandteil
- parallele DJI-Architekturpfade ohne gemeinsames M4-Domainmodell
- Secrets im Repository
