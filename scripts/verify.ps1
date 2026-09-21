param(
    [switch]$ResetVolumes,
    [switch]$Cleanup
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
Push-Location $repoRoot

try {
    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
        throw "Docker wurde nicht gefunden. Docker Desktop/Engine muss installiert und gestartet sein."
    }

    docker version | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "Docker Engine ist nicht erreichbar." }

    docker compose version | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "Docker Compose Plugin ist nicht verfügbar." }

    if (-not (Test-Path ".env")) {
        Copy-Item ".env.example" ".env"
        throw ".env wurde aus .env.example erstellt. Bitte POSTGRES_PASSWORD in .env setzen und den Befehl erneut ausführen."
    }

    if ($ResetVolumes) {
        Write-Warning "ResetVolumes entfernt die M4-Cloud PostgreSQL-, MQTT- und Monitoring-Volumes."
        docker compose --profile monitoring down -v --remove-orphans
        if ($LASTEXITCODE -ne 0) { throw "Alte Container/Volumes konnten nicht entfernt werden." }
    }

    Write-Host "1/5 Compose-Konfiguration prüfen..."
    docker compose config --quiet
    if ($LASTEXITCODE -ne 0) { throw "docker compose config fehlgeschlagen." }

    Write-Host "2/5 M4-Cloud bauen und starten..."
    docker compose up -d --build
    if ($LASTEXITCODE -ne 0) {
        docker compose ps
        docker compose logs --tail=200 --no-color
        throw "M4-Cloud konnte nicht vollständig gestartet werden."
    }

    Write-Host "3/5 Auf Readiness warten..."
    $ready = $false
    for ($i = 1; $i -le 40; $i++) {
        try {
            $response = Invoke-WebRequest -Uri "http://127.0.0.1:8080/ready" -UseBasicParsing -TimeoutSec 2
            if ($response.StatusCode -eq 200) {
                $ready = $true
                break
            }
        } catch {
            # Dienst ist während des Starts noch nicht bereit.
        }
        Start-Sleep -Seconds 2
    }

    if (-not $ready) {
        docker compose ps
        docker compose logs --tail=200 --no-color control-api integration-worker postgres mqtt reverse-proxy
        throw "M4-Cloud wurde nicht rechtzeitig bereit. Prüfe insbesondere PostgreSQL-Anmeldung und bestehende Volumes."
    }

    Write-Host "4/5 API-Endpunkte prüfen..."
    $health = Invoke-RestMethod "http://127.0.0.1:8080/health"
    $readiness = Invoke-RestMethod "http://127.0.0.1:8080/ready"
    $system = Invoke-RestMethod "http://127.0.0.1:8080/api/v1/system/status"
    $fh2 = Invoke-RestMethod "http://127.0.0.1:8080/api/v1/fh2/status"

    Write-Host "5/5 Dienststatus..."
    docker compose ps

    Write-Host ""
    Write-Host "Health:"
    $health | ConvertTo-Json -Depth 10
    Write-Host "Readiness:"
    $readiness | ConvertTo-Json -Depth 10
    Write-Host "System:"
    $system | ConvertTo-Json -Depth 10
    Write-Host "FH2:"
    $fh2 | ConvertTo-Json -Depth 10
    Write-Host ""
    Write-Host "M4-Cloud V1 acceptance passed."
}
finally {
    if ($Cleanup) {
        docker compose --profile monitoring down --remove-orphans
    }
    Pop-Location
}
