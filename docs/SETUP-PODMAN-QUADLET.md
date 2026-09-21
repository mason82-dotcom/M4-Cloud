# Podman + Quadlet unter WSL2

Dieser Pfad ergänzt den bestehenden Docker-Compose-Referenzbetrieb. Der Compose-Pfad bleibt die V1-Referenz, bis die Quadlet-Variante vollständig lokal und in CI abgenommen wurde.

## 1. Voraussetzungen

```bash
cat /etc/os-release
ps -p 1 -o comm=
podman --version
podman info --format '{{.Host.CgroupsVersion}}'
podman info --format '{{.Host.Security.Rootless}}'
```

Erwartet:

- `systemd` als PID 1
- Podman 5.x
- cgroup `v2`
- rootless `true`

Falls systemd unter WSL2 nicht aktiv ist:

```bash
sudo tee /etc/wsl.conf >/dev/null <<'EOF'
[boot]
systemd=true
EOF
```

Danach in PowerShell:

```powershell
wsl --shutdown
```

## 2. Pakete

```bash
sudo apt update
sudo apt install -y podman uidmap fuse-overlayfs slirp4netns
```

Registry-Test:

```bash
podman run --rm docker.io/library/hello-world
```

Die Warnung `"/" is not a shared mount` ist unter WSL2/rootless zunächst kein Abbruchgrund. Für die von M4 verwendeten normalen Bind-Mounts wird die Mount-Propagation nicht global verändert, solange kein konkreter Mountfehler auftritt.

## 3. Rootless-Zuordnungen

```bash
grep "^$USER:" /etc/subuid
grep "^$USER:" /etc/subgid
```

Falls beide fehlen:

```bash
sudo usermod --add-subuids 100000-165535 "$USER"
sudo usermod --add-subgids 100000-165535 "$USER"
```

Danach WSL neu starten.

## 4. Repository

Empfohlen ist der Linux-Checkout:

```bash
cd ~/src/M4-Cloud
git fetch --all --prune
git switch main
git pull --ff-only
```

Nicht den aktiven Linux-Entwicklungsbetrieb unter `/mnt/c` oder `/mnt/d` führen.

## 5. M4-Konfiguration

```bash
cd ~/src/M4-Cloud
cp -n .env.example .env
chmod 600 .env
nano .env
```

Mindestens:

```env
POSTGRES_PASSWORD=ein-langes-eigenes-passwort
```

Das Installationsskript kopiert die Runtime-Umgebung mit Modus 600 nach `~/.config/m4-cloud/m4.env`. Die Projektdatei `.env` bleibt Git-ignoriert.

## 6. Quadlet installieren

```bash
./scripts/m4-manager.sh install
```

Dabei werden:

1. Konfigurationsdateien nach `~/.config/m4-cloud/assets` kopiert.
2. die Control-API als `localhost/m4-control-api:current` gebaut.
3. die Quadlets aus `infra/quadlet/` rootless installiert.
4. `m4-cloud.target` als User-systemd-Target installiert.
5. der User-systemd-Manager neu geladen.

Für Podman 5.7 wird bewusst die kompatible Verzeichnisinstallation `podman quadlet install --replace <verzeichnis>` verwendet.

## 7. M4 Manager

Start:

```bash
./scripts/m4-manager.sh start
```

Status:

```bash
./scripts/m4-manager.sh status
```

Abnahme:

```bash
./scripts/m4-manager.sh verify
```

Logs:

```bash
./scripts/m4-manager.sh logs
```

Stop:

```bash
./scripts/m4-manager.sh stop
```

Optional Prometheus:

```bash
./scripts/m4-manager.sh monitoring-start
./scripts/m4-manager.sh monitoring-status
./scripts/m4-manager.sh monitoring-stop
```

Autostart im User-systemd-Manager:

```bash
./scripts/m4-manager.sh enable
```

Für Start ohne aktive Benutzeranmeldung kann zusätzlich `loginctl enable-linger "$USER"` aktiviert werden.

## 8. Dienste

| Unit | Container | Zweck |
| --- | --- | --- |
| `postgres.service` | `m4-postgres` | PostgreSQL |
| `mqtt.service` | `m4-mqtt` | MQTT |
| `control-api.service` | `m4-control-api` | FastAPI Control API |
| `integration-worker.service` | `m4-integration-worker` | MQTT Worker |
| `reverse-proxy.service` | `m4-reverse-proxy` | Nginx / HTTP |
| `prometheus.service` | `m4-prometheus` | optionales Monitoring |

PostgreSQL, MQTT, Control API und Nginx verwenden Healthchecks. `Notify=healthy` sorgt dafür, dass abhängige systemd-Units erst weiterstarten, wenn der jeweilige Container gesund ist.

## 9. Ports

Der erste Quadlet-Pfad verwendet die V1-Standardports:

- HTTP: `0.0.0.0:8080`
- MQTT: `127.0.0.1:1883`
- Prometheus: `127.0.0.1:9090`

Die Compose-Variablen `M4_HTTP_PORT`, `M4_MQTT_PORT` und `PROMETHEUS_PORT` gelten aktuell nur für den Compose-Pfad. Dynamische Quadlet-Port-Overrides werden erst ergänzt, wenn der Basispfad vollständig abgenommen ist.

## 10. VS Code

Aus Ubuntu:

```bash
cd ~/src/M4-Cloud
code .
```

Empfohlene Erweiterungen stehen in `.vscode/extensions.json`.

Zusätzlich stehen Tasks zur Verfügung:

- `M4: Podman installieren/aktualisieren`
- `M4: Start`
- `M4: Stop`
- `M4: Status`
- `M4: Abnahme`
- `M4: Logs`
- `M4: Monitoring starten`

Aufruf über **Terminal -> Run Task** bzw. **Tasks: Run Task**.

## 11. Architektur

```text
docker-compose.yml
  = getestete V1-Referenz

infra/quadlet/
  m4.network
  postgres-data.volume
  mqtt-data.volume
  prometheus-data.volume
  postgres.container
  mqtt.container
  control-api.container
  integration-worker.container
  reverse-proxy.container
  prometheus.container

infra/systemd/
  m4-cloud.target

scripts/
  quadlet-install.sh
  m4-manager.sh
  verify-quadlet.sh
```

Der Quadlet-Pfad bleibt getrennt vom Compose-Pfad, sodass beide Varianten unabhängig getestet und zurückgerollt werden können.
