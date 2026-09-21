# Security

## V1 Defaults

- Keine Secrets werden committed; `.env` ist ignoriert.
- PostgreSQL und Control API haben keine Host-Port-Freigabe.
- MQTT ist auf Host-Loopback beschränkt.
- Prometheus ist auf Host-Loopback beschränkt.
- FH2-Zugangsdaten werden weder im Status-Endpunkt noch in Logs ausgegeben.
- TLS-Verifikation zum FH2-Upstream ist standardmäßig aktiv.

## Produktion

Vor einer Freigabe über ein vertrauenswürdiges LAN hinaus:

1. TLS am Reverse Proxy terminieren.
2. Authentifizierung/Autorisierung vor die M4-Control-API setzen.
3. MQTT mit Benutzer-/Zertifikatsauthentifizierung und TLS absichern.
4. Firewall-Regeln auf notwendige Quellen begrenzen.
5. Regelmäßige PostgreSQL-/Volume-Backups testen.
6. DJI-Lizenz-, OpenAPI- und Zertifikatsmaterial nur über lokale
   Secret-Mechanismen bereitstellen.

Die V1 ist für einen kontrollierten On-Premises-/Heimnetz-Betrieb vorgesehen,
nicht für eine ungeschützte Veröffentlichung im Internet.
