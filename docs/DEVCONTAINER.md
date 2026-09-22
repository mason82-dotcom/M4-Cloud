# Dev Container

M4-Cloud stellt eine schlanke VS-Code-Entwicklungsumgebung bereit.

## Ziel

Der Dev Container enthält nur Entwicklungswerkzeuge:

- Python 3.12 auf Debian Bookworm
- pytest
- Ruff
- PostgreSQL-Client
- Mosquitto-Clients
- curl
- jq
- ShellCheck
- VS-Code-Python-/YAML-/Container-Erweiterungen

PostgreSQL, Mosquitto, Nginx und andere M4-Runtime-Dienste werden **nicht**
noch einmal innerhalb des Dev Containers gestartet.

Damit bleibt die Trennung klar:

```text
WSL2 Ubuntu
├── Podman / M4 Runtime
│   ├── PostgreSQL
│   ├── MQTT
│   ├── Control API
│   └── weitere Dienste
│
└── VS Code Dev Container
    ├── Python 3.12
    ├── pytest / Ruff
    ├── Client-Werkzeuge
    └── M4-Quellcode
```

## Voraussetzung unter WSL2 + Podman

Podman 5+ muss im WSL-Ubuntu funktionieren:

```bash
podman --version
podman info --format '{{.Host.Security.Rootless}}'
podman run --rm docker.io/library/hello-world
```

In den **VS-Code-Benutzereinstellungen der WSL-Umgebung** setzen:

```json
{
  "dev.containers.dockerPath": "podman"
}
```

Diese Einstellung gehört bewusst nicht ins Repository, weil sie vom lokalen
Container-Backend des Entwicklers abhängt.

## Öffnen

Aus WSL:

```bash
cd ~/src/M4-Cloud
code .
```

Dann in VS Code:

```text
Strg+Shift+P
Dev Containers: Reopen in Container
```

VS Code baut `.devcontainer/Dockerfile` und führt anschließend automatisch
`.devcontainer/post-create.sh` aus.

## Python-Umgebung

Beim ersten Start entsteht lokal im Workspace:

```text
.venv/
```

Installiert werden die Abhängigkeiten aus:

```text
services/control-api/requirements-dev.txt
```

Die Datei `.venv/` ist bereits Git-ignoriert.

## Lokale Codeprüfung

Im Dev Container:

```bash
./scripts/dev-check.sh
```

Der Check führt aus:

1. Ruff gegen `app` und `tests`
2. pytest gegen die Control-API-Tests

Dieser Entwicklercheck ist **keine zentrale CI**.

## Director-CI

Die GitHub-Actions-Validation bleibt ausschließlich beim Direktor und wird
manuell über `workflow_dispatch` gestartet.

Der Dev Container:

- startet keine GitHub Actions,
- verändert den Director-Workflow nicht,
- merged nicht selbst nach `main`.

## Runtime testen

Der Dev Container ersetzt den M4-Runtime-Test nicht. Der eigentliche Stack
wird weiterhin außerhalb des Dev Containers mit dem dafür vorgesehenen
Runtime-Pfad gestartet.

Das vermeidet eine verschachtelte Container-Runtime und zusätzliche Probleme
mit cgroups, Sockets, UID/GID und Volumes.

## Basisimage

Verwendet wird:

```text
mcr.microsoft.com/devcontainers/python:3.12-bookworm
```

Das hält die Entwicklungs-Python-Version passend zur M4-Control-API auf
Python 3.12.
