#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cmd="${1:-help}"

status() {
  systemctl --user --no-pager --full status     m4-cloud.target     postgres.service mqtt.service control-api.service     integration-worker.service reverse-proxy.service || true
  echo
  podman ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
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
    journalctl --user       -u postgres.service       -u mqtt.service       -u control-api.service       -u integration-worker.service       -u reverse-proxy.service       -n 200 -f
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
  *)
    cat <<'EOF'
M4-Cloud Manager

Nutzung:
  scripts/m4-manager.sh install
  scripts/m4-manager.sh start
  scripts/m4-manager.sh stop
  scripts/m4-manager.sh restart
  scripts/m4-manager.sh status
  scripts/m4-manager.sh ps
  scripts/m4-manager.sh logs
  scripts/m4-manager.sh verify
  scripts/m4-manager.sh monitoring-start
  scripts/m4-manager.sh monitoring-stop
  scripts/m4-manager.sh monitoring-status
  scripts/m4-manager.sh enable
  scripts/m4-manager.sh disable
EOF
    ;;
esac
