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
need python3

if [[ ! -f "$env_file" ]]; then
  cp "$repo_root/.env.example" "$env_file"
  chmod 600 "$env_file"
fi

if grep -Eq '^POSTGRES_PASSWORD=(CHANGE_ME)?$' "$env_file"; then
  echo "POSTGRES_PASSWORD in .env ist noch nicht gesetzt." >&2
  exit 2
fi

ensure_secret() {
  local key="$1"
  local current
  current="$(grep -E "^$key=" "$env_file" | tail -n 1 | cut -d= -f2- || true)"
  if [[ -z "$current" || "$current" == "CHANGE_ME" ]]; then
    local value
    value="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
    if grep -qE "^$key=" "$env_file"; then
      sed -i "s|^$key=.*|$key=$value|" "$env_file"
    else
      printf '\n%s=%s\n' "$key" "$value" >> "$env_file"
    fi
    echo "$key wurde lokal generiert."
  fi
}

ensure_uuid() {
  local key="$1"
  local current
  current="$(grep -E "^$key=" "$env_file" | tail -n 1 | cut -d= -f2- || true)"
  if [[ -z "$current" || "$current" == "CHANGE_ME" ]]; then
    local value
    value="$(python3 -c 'import uuid; print(uuid.uuid4())')"
    if grep -qE "^$key=" "$env_file"; then
      sed -i "s|^$key=.*|$key=$value|" "$env_file"
    else
      printf '\n%s=%s\n' "$key" "$value" >> "$env_file"
    fi
    echo "$key wurde lokal generiert."
  fi
}

ensure_secret MQTT_WORKER_PASSWORD
ensure_secret MQTT_HEALTH_PASSWORD
ensure_secret DJI_BOOTSTRAP_TOKEN
ensure_secret DJI_API_TOKEN
ensure_secret DJI_WS_TOKEN
ensure_secret DJI_MQTT_PASSWORD
ensure_uuid DJI_WORKSPACE_ID

chmod 600 "$env_file"
mkdir -p "$m4_config/assets" "$user_systemd"

install -m 600 "$env_file" "$m4_config/m4.env"
install -m 644 "$repo_root/infra/nginx/nginx.conf" "$m4_config/assets/nginx.conf"
install -m 644 "$repo_root/infra/postgres/init.sql" "$m4_config/assets/init.sql"
install -m 644 "$repo_root/infra/prometheus/prometheus.yml" "$m4_config/assets/prometheus.yml"
install -m 644 "$repo_root/infra/systemd/m4-cloud.target" "$user_systemd/m4-cloud.target"

echo "Baue M4 Control API..."
podman build -t localhost/m4-control-api:current "$repo_root/services/control-api"

echo "Baue sicheren M4 MQTT Broker..."
podman build -t localhost/m4-mqtt:current "$repo_root/infra/mosquitto"

echo "Installiere/aktualisiere Quadlets..."
podman quadlet install --replace "$repo_root/infra/quadlet"

systemctl --user daemon-reload

echo
echo "Quadlet-Installation abgeschlossen."
echo "Start:  $repo_root/scripts/m4-manager.sh start"
echo "Status: $repo_root/scripts/m4-manager.sh status"
echo "DJI Bootstrap-Status: http://127.0.0.1:8080/api/v1/dji/cloud/status"
