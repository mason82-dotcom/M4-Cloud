# Setup unter WSL2 + Ubuntu + WSLC

Diese Anleitung beschreibt den empfohlenen Windows-Entwicklungsweg für M4-Cloud sowie den optionalen Einsatz von **WSLC** (`wslc.exe`) als Docker-Desktop-freie Container-Laufzeit.

> Stand: September 2026. WSLC ist noch ein WSL-Pre-Release-Feature. Für den produktiven M4-V1-Stack bleibt `docker compose` der vollständig getestete Referenzpfad. WSLC wird parallel als experimenteller Runtime-Pfad vorbereitet.

## 1. Voraussetzungen unter Windows

PowerShell **als Administrator** öffnen:

```powershell
wsl --install -d Ubuntu
```

Falls Windows einen Neustart verlangt, neu starten.

Danach WSL auf die für WSLC notwendige Pre-Release-Version aktualisieren:

```powershell
wsl --update --pre-release
wsl --shutdown
wsl --version
wsl -l -v
```

Erwartet:

- WSL 2.9.3 oder neuer
- Ubuntu läuft als Version 2

WSLC prüfen:

```powershell
wslc version
wslc run --rm hello-world
```

Wenn `wslc` nicht gefunden wird:

```powershell
wsl --update --pre-release
wsl --shutdown
```

Danach PowerShell neu öffnen.

Offizielle Microsoft-Dokumentation:

- https://learn.microsoft.com/windows/wsl/wsl-container
- https://learn.microsoft.com/windows/wsl/tutorials/wsl-containers
- https://learn.microsoft.com/windows/wsl/setup/environment

## 2. Ubuntu-Grundsystem vorbereiten

Ubuntu öffnen:

```bash
sudo apt update
sudo apt full-upgrade -y
sudo apt install -y git curl ca-certificates jq make python3 python3-venv
```

Prüfen:

```bash
uname -a
git --version
python3 --version
```

## 3. Projekt im Linux-Dateisystem ablegen

Für WSL-Entwicklung das Repository möglichst **nicht** dauerhaft unter `/mnt/c` oder `/mnt/d` bearbeiten.

Empfohlen:

```bash
mkdir -p ~/src
cd ~/src
git clone https://github.com/mason82-dotcom/M4-Cloud.git
cd M4-Cloud
```

Windows kann auf das Verzeichnis über folgenden Pfad zugreifen:

```text
\\wsl$\Ubuntu\home\<linux-user>\src\M4-Cloud
```

## 4. VS Code mit Ubuntu/WSL2

VS Code unter Windows installieren und die Erweiterung **WSL** aktivieren.

Im Ubuntu-Terminal:

```bash
cd ~/src/M4-Cloud
code .
```

Im VS-Code-Fenster muss links unten eine WSL-Verbindung zu Ubuntu angezeigt werden.

Empfohlene Erweiterungen:

- WSL
- Python
- GitHub Pull Requests and Issues
- YAML
- optional Podman/Quadlet, falls später der Podman-Pfad genutzt wird

## 5. M4-Konfiguration

Im Projekt:

```bash
cp .env.example .env
nano .env
```

Mindestens ein eigenes PostgreSQL-Passwort setzen:

```env
POSTGRES_PASSWORD=ein-langes-eigenes-passwort
```

Wichtig:

- `.env` niemals committen.
- Das Passwort nach der ersten PostgreSQL-Initialisierung nicht einfach ändern, solange das vorhandene PostgreSQL-Volume weiterverwendet wird.
- Bei einem bewusst neuen Testsystem kann das Volume gelöscht und neu angelegt werden.

## 6. Referenzpfad: M4 V1 unter WSL2

Der aktuell vollständig getestete V1-Stack verwendet Compose.

Wenn Docker Engine/Compose bereits in Ubuntu verfügbar ist:

```bash
docker version
docker compose version
docker compose up -d --build
docker compose ps
```

Abnahme:

```bash
sh scripts/verify.sh
```

Status:

```bash
curl http://127.0.0.1:8080/health
curl http://127.0.0.1:8080/ready
curl http://127.0.0.1:8080/api/v1/system/status
curl http://127.0.0.1:8080/api/v1/fh2/status
```

Von Windows ist der Reverse Proxy standardmäßig erreichbar unter:

```text
http://localhost:8080
```

## 7. WSLC verwenden

WSLC wird von Windows bereitgestellt. Es braucht keine separate Docker-Desktop-Engine.

Grundtest aus PowerShell:

```powershell
wslc run --rm hello-world
wslc image list
wslc container list
```

Ein einfacher Nginx-Test:

```powershell
wslc run -d --rm -p 8088:80 --name m4-wslc-test nginx:alpine
curl.exe http://localhost:8088
wslc container logs m4-wslc-test
wslc container stop m4-wslc-test
```

Control-API-Image bauen:

```powershell
cd D:\Pfad\zu\M4-Cloud\services\control-api
wslc build -t m4-control-api .
wslc image list
```

Alternativ das Repository in Ubuntu öffnen und den Windows-Befehl aus WSL aufrufen:

```bash
wslc.exe version
wslc.exe image list
```

## 8. Wichtige Einschränkung von WSLC für M4 V1

Die offizielle WSLC-Dokumentation beschreibt aktuell Container-, Image-, Build-, Exec- und Port-Funktionen, aber keinen nativen Ersatz für `docker compose`.

M4 V1 besteht aus mehreren koordinierten Diensten:

- reverse-proxy
- control-api
- integration-worker
- postgres
- mqtt
- optional prometheus

Deshalb wird `docker-compose.yml` **nicht blind durch einzelne `wslc run`-Befehle ersetzt**. Dafür müssten Netzwerke, Persistenz, Abhängigkeiten, Healthchecks und Startreihenfolge ausdrücklich nachgebildet und getestet werden.

Für M4 gilt deshalb:

1. **V1 Referenz / stabil:** Compose unter Linux/WSL2.
2. **Docker-Desktop-frei, stabiler Kandidat:** Podman + Quadlet/Compose-Kompatibilität.
3. **WSLC:** experimenteller Microsoft-Runtime-Pfad; Migration erst nach vollständiger Multi-Service-Abnahme.

Ein inoffizielles Projekt namens `wslc-compose` existiert, ist aber kein Microsoft-Bestandteil und wird deshalb nicht als V1-Abhängigkeit vorausgesetzt.

## 9. Aktuelles Windows-Passwort-/Volume-Problem beheben

Wenn PostgreSQL healthy ist, aber `control-api` und `integration-worker` ständig neu starten, zuerst Logs prüfen:

```powershell
docker compose logs --tail=200 control-api integration-worker postgres
```

Wenn dort PostgreSQL-Authentifizierungsfehler erscheinen, kann ein altes Volume mit einem anderen Passwort vorhanden sein.

Nur wenn die vorhandenen M4-Testdaten gelöscht werden dürfen:

```powershell
Remove-Item Env:POSTGRES_PASSWORD -ErrorAction SilentlyContinue
docker compose --profile monitoring down -v --remove-orphans
docker compose up -d --build
docker compose ps
```

Unter Ubuntu:

```bash
docker compose --profile monitoring down -v --remove-orphans
docker compose up -d --build
docker compose ps
```

## 10. PowerShell-Abnahme

Nach Aktualisierung des Repositories steht zusätzlich zur Linux-Abnahme zur Verfügung:

```powershell
.\scripts\verify.ps1
```

Für einen bewusst frischen Test mit neu angelegten Volumes:

```powershell
.\scripts\verify.ps1 -ResetVolumes
```

Achtung: `-ResetVolumes` löscht die M4-Datenvolumes.

## 11. Git-Workflow

Vor der Arbeit:

```bash
git switch main
git pull --ff-only
git status
```

Für Entwicklungsarbeiten nicht direkt auf `main` committen. Der FH2-Arbeitsbranch ist:

```bash
git switch agent/fh2-onprem-control
git pull --ff-only
```

Der Direktor integriert geprüfte Änderungen über:

```text
agent/fullstack-integration
```
