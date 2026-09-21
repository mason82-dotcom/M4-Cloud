# WSL2, Ubuntu, VS Code und WSLC

## Runtime-Entscheidung

```text
Podman + Quadlet   empfohlen für M4
Docker Compose     Referenz/Director Validation
WSLC               optional/experimentell
```

Docker Desktop ist für den bevorzugten lokalen M4-Pfad nicht erforderlich.

## WSL2 prüfen

PowerShell:

```powershell
wsl --version
wsl -l -v
```

Ubuntu:

```bash
ps -p 1 -o comm=
```

Erwartet: `systemd`.

## Repository

```bash
mkdir -p ~/src
cd ~/src
git clone https://github.com/mason82-dotcom/M4-Cloud.git
cd M4-Cloud
```

Projekt im Linux-Dateisystem betreiben, nicht dauerhaft unter `/mnt/c` oder `/mnt/d`.

## VS Code

```bash
cd ~/src/M4-Cloud
code .
```

Erwartet: `WSL: Ubuntu`.

## Podman

```bash
sudo apt install -y podman uidmap fuse-overlayfs slirp4netns
podman run --rm docker.io/library/hello-world

cp -n .env.example .env
chmod 600 .env
nano .env

./scripts/m4-manager.sh install
./scripts/m4-manager.sh start
./scripts/m4-manager.sh verify
```

## WSLC

WSLC kann parallel für Einzelcontainer-Experimente verwendet werden, ist aber nicht die primäre M4-Multi-Service-Runtime.

Wenn Registry-Zugriffe über IPv6 scheitern, reicht für M4 funktionierendes IPv4. M4 benötigt lokal kein IPv6.

## CI-Rolle

GitHub Actions wird nicht automatisch durch Manager-Arbeit gestartet. Nur der Direktor startet die zentrale Validation manuell.
