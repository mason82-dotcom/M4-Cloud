#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

command -v podman >/dev/null 2>&1 || {
  echo "Podman wurde nicht gefunden." >&2
  exit 1
}

systemctl --user start m4-cloud.target

attempt=0
until curl --fail --silent http://127.0.0.1:8080/ready >/dev/null; do
  attempt=$((attempt + 1))
  if (( attempt >= 40 )); then
    echo "M4-Cloud wurde nicht rechtzeitig ready." >&2
    "$repo_root/scripts/m4-manager.sh" status
    journalctl --user       -u postgres.service       -u mqtt.service       -u control-api.service       -u integration-worker.service       -u reverse-proxy.service       -n 200 --no-pager
    exit 1
  fi
  sleep 2
done

echo "Health:"
curl --fail --silent http://127.0.0.1:8080/health
echo

echo "Ready:"
curl --fail --silent http://127.0.0.1:8080/ready
echo

echo "Systemstatus:"
curl --fail --silent http://127.0.0.1:8080/api/v1/system/status
echo

echo "FH2-Status:"
curl --fail --silent http://127.0.0.1:8080/api/v1/fh2/status
echo

echo
podman ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
echo
echo "M4-Cloud Quadlet-Abnahme erfolgreich."
