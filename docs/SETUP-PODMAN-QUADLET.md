# Podman + Quadlet unter WSL2

Dieser Pfad ergänzt den bestehenden Docker-Compose-Referenzbetrieb. Er ersetzt ihn nicht, solange der vollständige M4-Stack noch nicht mit Quadlet abgenommen wurde.

## 1. Voraussetzungen prüfen

```bash
cat /etc/os-release
ps -p 1 -o comm=
```

Für Quadlet muss `systemd` als PID 1 laufen.

Falls nicht:

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

## 2. Podman installieren

Unter Ubuntu:

```bash
sudo apt update
sudo apt install -y podman uidmap fuse-overlayfs slirp4netns
```

Prüfen:

```bash
podman --version
podman info --format '{{.Host.CgroupsVersion}}'
podman info --format '{{.Host.Security.Rootless}}'
```

Erwartet:

- cgroup v2
- rootless = true, wenn Podman als normaler Benutzer gestartet wird

## 3. Registry-/Netzwerktest

```bash
podman run --rm docker.io/library/hello-world
```

Falls der Abruf scheitert, zuerst IPv4 testen:

```bash
curl -4 -I https://registry-1.docker.io/v2/
```

HTTP 401 ist bei diesem Registry-Test erwartbar und zeigt, dass die Verbindung funktioniert.

## 4. Rootless-Zuordnungen prüfen

```bash
grep "^$USER:" /etc/subuid
grep "^$USER:" /etc/subgid
```

Falls keine Einträge vorhanden sind:

```bash
sudo usermod --add-subuids 100000-165535 "$USER"
sudo usermod --add-subgids 100000-165535 "$USER"
```

Danach WSL neu starten.

## 5. Quadlet-Benutzerpfad

```bash
mkdir -p ~/.config/containers/systemd
systemctl --user daemon-reload
```

Rootless Quadlet-Dateien werden dort als Benutzer-Units verarbeitet.

## 6. VS Code

Repository aus Ubuntu öffnen:

```bash
cd ~/src/M4-Cloud
code .
```

Empfohlene Erweiterungen sind in `.vscode/extensions.json` hinterlegt.

## 7. M4-Konfiguration

```bash
cd ~/src/M4-Cloud
cp -n .env.example .env
chmod 600 .env
nano .env
```

Mindestens `POSTGRES_PASSWORD` auf ein eigenes Passwort setzen.

## 8. Architektur

Der bestehende Pfad bleibt:

```text
docker-compose.yml
  = getestete V1-Referenz
```

Der neue Pfad wird separat aufgebaut:

```text
infra/quadlet/
  m4.network
  postgres.volume
  mqtt.volume
  prometheus.volume
  postgres.container
  mqtt.container
  control-api.container
  integration-worker.container
  reverse-proxy.container
  prometheus.container
```

Erst nach vollständiger Abnahme wird dieser Pfad als gleichwertige Runtime dokumentiert.
