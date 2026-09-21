#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
env_file="$repo_root/.env"
config_root="${XDG_CONFIG_HOME:-$HOME/.config}"
m4_config="$config_root/m4-cloud"
user_systemd="$config_root/systemd/user"

need() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "Fehlt: $1" >&2
    exit 1
  }
}

need podman
need systemctl
need install

if [[ ! -f "$env_file" ]]; then
  cp "$repo_root/.env.example" "$env_file"
  chmod 600 "$env_file"
  echo ".env wurde aus .env.example erstellt."
  echo "Bitte POSTGRES_PASSWORD in $env_file setzen und das Skript erneut starten."
  exit 2
fi

if grep -Eq '^POSTGRES_PASSWORD=(CHANGE_ME)?$' "$env_file"; then
  echo "POSTGRES_PASSWORD in .env ist noch nicht gesetzt." >&2
  exit 2
fi

mkdir -p "$m4_config/assets" "$user_systemd"

install -m 600 "$env_file" "$m4_config/m4.env"
install -m 644 "$repo_root/infra/nginx/nginx.conf" "$m4_config/assets/nginx.conf"
install -m 644 "$repo_root/infra/mosquitto/mosquitto.conf" "$m4_config/assets/mosquitto.conf"
install -m 644 "$repo_root/infra/postgres/init.sql" "$m4_config/assets/init.sql"
install -m 644 "$repo_root/infra/prometheus/prometheus.yml" "$m4_config/assets/prometheus.yml"
install -m 644 "$repo_root/infra/systemd/m4-cloud.target" "$user_systemd/m4-cloud.target"

echo "Baue M4 Control API..."
podman build -t localhost/m4-control-api:current "$repo_root/services/control-api"

echo "Installiere/aktualisiere Quadlets..."
podman quadlet install --replace "$repo_root/infra/quadlet"

systemctl --user daemon-reload

echo
echo "Quadlet-Installation abgeschlossen."
echo "Start:  $repo_root/scripts/m4-manager.sh start"
echo "Status: $repo_root/scripts/m4-manager.sh status"
