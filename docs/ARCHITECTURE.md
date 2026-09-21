# Architektur

## Systemgrenze

M4-Cloud ist der eigene Integrations- und Kontroll-Layer. DJI FlightHub 2
On-Premises bleibt ein externer, offiziell bezogener Upstream.

```text
DJI Pilot 2 / DJI Dock / FH2 On-Premises
                  |
        offizielle Schnittstellen
      MQTT / HTTPS / WebSocket / OpenAPI
                  |
             [M4-Cloud]
                  |
       +----------+----------+
       |                     |
  Reverse Proxy          MQTT Broker
       |
   Control API
       |
   PostgreSQL
```

## Eigene Komponenten

- **Reverse Proxy:** zentraler HTTP-Einstieg und WebSocket-Passthrough.
- **Control API:** Liveness, Readiness, Systemstatus und spätere Adapter.
- **PostgreSQL:** ausschließlich M4-eigene Zustände und Konfigurationen.
- **MQTT:** Integrationspunkt für offiziell unterstützte DJI-Cloud-API-Flows.

## Nicht Bestandteil des Repositories

- DJI FlightHub 2 On-Premises Binärdateien, Container oder Installationspakete
- DJI-interne Services
- Lizenzdateien
- proprietäre Implementierungen aus Reverse Engineering

## Integrationsprinzip

Adapter werden ausschließlich gegen dokumentierte oder offiziell freigegebene
Schnittstellen gebaut. Der FH2-Upstream wird über Konfiguration referenziert.
M4-Cloud muss ohne erreichbaren FH2-Upstream startfähig und diagnostizierbar
bleiben.

## V1-Verantwortungsgrenze

V1 stellt den lokalen Kontrollserver-Rahmen bereit. Eine konkrete DJI-Instanz
wird erst über deren offiziell bereitgestellte Parameter, Zertifikate und
Zugangsdaten angebunden. Diese Daten gehören nicht ins Repository.
