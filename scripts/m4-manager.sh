#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cmd="${1:-help}"
base_url="${M4_BASE_URL:-http://127.0.0.1:8080}"

status() {
  systemctl --user --no-pager --full status \
    m4-cloud.target \
    postgres.service mqtt.service control-api.service \
    integration-worker.service reverse-proxy.service || true
  echo
  podman ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
}

curl_json() {
  curl --fail --silent --show-error "$@"
  echo
}

case "$cmd" in
  install)
    exec "$repo_root/scripts/quadlet-install.sh"
    ;;
  start)
    systemctl --user start m4-cloud.target
    ;;
  stop)
    systemctl --user stop m4-cloud.target
    ;;
  restart)
    systemctl --user restart m4-cloud.target
    ;;
  status)
    status
    ;;
  ps)
    podman ps
    ;;
  logs)
    journalctl --user \
      -u postgres.service \
      -u mqtt.service \
      -u control-api.service \
      -u integration-worker.service \
      -u reverse-proxy.service \
      -n 200 -f
    ;;
  monitoring-start)
    systemctl --user start prometheus.service
    ;;
  monitoring-stop)
    systemctl --user stop prometheus.service
    ;;
  monitoring-status)
    systemctl --user --no-pager --full status prometheus.service || true
    ;;
  enable)
    systemctl --user enable m4-cloud.target
    echo "Autostart für den User-Manager ist aktiviert."
    echo "Für Start ohne aktive Anmeldung optional: loginctl enable-linger $USER"
    ;;
  disable)
    systemctl --user disable m4-cloud.target
    ;;
  verify)
    exec "$repo_root/scripts/verify-quadlet.sh"
    ;;
  camera-status)
    curl_json "$base_url/api/v1/cameras/status"
    ;;
  camera-paths)
    curl_json "$base_url/api/v1/cameras/paths"
    ;;
  camera-telemetry)
    curl_json "$base_url/api/v1/cameras/telemetry"
    ;;
  dji-cloud-status)
    curl_json "$base_url/api/v1/dji/cloud/status"
    ;;
  fh2-status)
    curl_json "$base_url/api/v1/fh2/status"
    ;;
  fh2-devices)
    device_class="${2:-airport}"
    case "$device_class" in
      airport|drone|base_station) ;;
      *)
        echo "Geräteklasse muss airport, drone oder base_station sein." >&2
        exit 2
        ;;
    esac
    curl_json "$base_url/api/v1/fh2/devices?device_class=$device_class"
    ;;
  fh2-hms)
    device_sn="${2:-}"
    if [[ -z "$device_sn" ]]; then
      echo "Nutzung: scripts/m4-manager.sh fh2-hms <DEVICE_SN>" >&2
      exit 2
    fi
    curl_json --get --data-urlencode "device_sn=$device_sn" "$base_url/api/v1/fh2/hms"
    ;;
  fh2-waylines)
    curl_json "$base_url/api/v1/fh2/waylines"
    ;;
  fh2-tasks)
    device_sn="${2:-}"
    if [[ -n "$device_sn" ]]; then
      curl_json --get --data-urlencode "sn=$device_sn" "$base_url/api/v1/fh2/flight-tasks"
    else
      curl_json "$base_url/api/v1/fh2/flight-tasks"
    fi
    ;;
  fh2-verify)
    echo "FH2 Status:"
    curl_json "$base_url/api/v1/fh2/status"
    echo "Geräte:"
    curl_json "$base_url/api/v1/fh2/devices?device_class=airport&page_size=1"
    echo "Waylines:"
    curl_json "$base_url/api/v1/fh2/waylines?page_size=1"
    echo "Flight Tasks:"
    curl_json "$base_url/api/v1/fh2/flight-tasks?page_size=1"
    echo "FH2 OpenAPI V2 Read-Only-Verifikation erfolgreich."
    ;;
  *)
    cat <<'EOF'
M4-Cloud Manager

Stack:
  scripts/m4-manager.sh install
  scripts/m4-manager.sh start
  scripts/m4-manager.sh stop
  scripts/m4-manager.sh restart
  scripts/m4-manager.sh status
  scripts/m4-manager.sh ps
  scripts/m4-manager.sh logs
  scripts/m4-manager.sh verify

Monitoring:
  scripts/m4-manager.sh monitoring-start
  scripts/m4-manager.sh monitoring-stop
  scripts/m4-manager.sh monitoring-status

Autostart:
  scripts/m4-manager.sh enable
  scripts/m4-manager.sh disable

DJI Cloud API / Kamera (read-only):
  scripts/m4-manager.sh dji-cloud-status
  scripts/m4-manager.sh camera-status
  scripts/m4-manager.sh camera-paths
  scripts/m4-manager.sh camera-telemetry

DJI FlightHub 2 OpenAPI V2 (read-only):
  scripts/m4-manager.sh fh2-status
  scripts/m4-manager.sh fh2-devices [airport|drone|base_station]
  scripts/m4-manager.sh fh2-hms <DEVICE_SN>
  scripts/m4-manager.sh fh2-waylines
  scripts/m4-manager.sh fh2-tasks [DEVICE_SN]
  scripts/m4-manager.sh fh2-verify
EOF
    ;;
esac
