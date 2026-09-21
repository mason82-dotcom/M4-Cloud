# Podman + Quadlet unter WSL2

Podman + Quadlet ist der empfohlene Docker-Desktop-freie Runtime-Pfad für M4 unter WSL2/Ubuntu.

## Voraussetzungen

```bash
ps -p 1 -o comm=
podman --version
podman info --format '{{.Host.CgroupsVersion}}'
podman info --format '{{.Host.Security.Rootless}}'
```

Erwartet:

- systemd
- cgroup v2
- rootless true

## Installation

```bash
sudo apt update
sudo apt install -y podman uidmap fuse-overlayfs slirp4netns
podman run --rm docker.io/library/hello-world
```

## M4

```bash
cd ~/src/M4-Cloud
cp -n .env.example .env
chmod 600 .env
nano .env
```

Mindestens `POSTGRES_PASSWORD` manuell setzen.

Danach:

```bash
./scripts/m4-manager.sh install
./scripts/m4-manager.sh start
./scripts/m4-manager.sh verify
```

Der Installer:

1. erzeugt fehlende interne Secrets
2. erzeugt eine Workspace-UUID
3. baut Control API
4. baut den gehärteten M4-Mosquitto
5. installiert rootless Quadlets
6. lädt systemd user neu

## Automatisch erzeugte Werte

- `MQTT_WORKER_PASSWORD`
- `MQTT_HEALTH_PASSWORD`
- `DJI_BOOTSTRAP_TOKEN`
- `DJI_API_TOKEN`
- `DJI_WS_TOKEN`
- `DJI_MQTT_PASSWORD`
- `DJI_WORKSPACE_ID`

Nicht automatisch:

- `DJI_APP_ID`
- `DJI_APP_KEY`
- `DJI_APP_LICENSE`

## Ports

```text
0.0.0.0:8080
127.0.0.1:1883
127.0.0.1:9090
```

MQTT ist authentifiziert, aber noch kein TLS-LAN-Zugang für DJI Pilot 2.

## Manager

```bash
./scripts/m4-manager.sh status
./scripts/m4-manager.sh verify
./scripts/m4-manager.sh dji-cloud-status
./scripts/m4-manager.sh camera-telemetry
```

## Autostart

```bash
./scripts/m4-manager.sh enable
sudo loginctl enable-linger "$USER"
```

Compose bleibt als Referenzpfad; zentrale CI wird ausschließlich vom Direktor manuell gestartet.
