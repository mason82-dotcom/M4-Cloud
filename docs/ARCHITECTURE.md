# Architektur

## Zielbild

M4-Cloud besitzt ein eigenes Domainmodell. Externe DJI-Schnittstellen dürfen dieses Modell nicht bestimmen.

```text
FlightHub 2 ─ OpenAPI V2 Adapter ─┐
                                 ├─ M4 Domainmodell ─ Control API
RC Pro/Aircraft ─ Cloud API Adapter┘                 ├─ PostgreSQL
                                                     └─ MQTT
```

## Regeln

1. FH2 OpenAPI V2 und DJI Cloud API sind getrennte Integrationspfade.
2. MSDK V5 kann als dritter Adapter angebunden werden.
3. Kamera-/Gimbal-/Gerätezustände werden auf kanonische M4-Modelle normalisiert.
4. Keine DJI-spezifischen Pfade im Frontend.
5. Keine direkte Kopplung an M3-Cloud.
6. Lyrebird ist deaktiviert.
7. DRC und aktive Flugsteuerung werden erst nach separater Freigabe aktiviert.

## Basisdienste

- `control-api`: FastAPI, Adaptergrenzen und Domainmodell.
- `mqtt`: interner Mosquitto-Broker, authentifiziert und ACL-beschränkt.
- `postgres`: Persistenz; fachliches Schema folgt erst mit stabilen Domänenobjekten.
