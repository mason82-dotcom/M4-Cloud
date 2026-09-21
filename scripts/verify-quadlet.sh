#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
base_url="http://127.0.0.1:8080"

command -v podman >/dev/null 2>&1 || {
  echo "Podman wurde nicht gefunden." >&2
  exit 1
}

command -v curl >/dev/null 2>&1 || {
  echo "curl wurde nicht gefunden." >&2
  exit 1
}

systemctl --user start m4-cloud.target

attempt=0
until curl --fail --silent "$base_url/ready" >/dev/null; do
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
curl --fail --silent "$base_url/health"
echo

echo "Ready:"
curl --fail --silent "$base_url/ready"
echo

echo "Systemstatus:"
curl --fail --silent "$base_url/api/v1/system/status"
echo

echo "DJI Cloud API Status:"
curl --fail --silent "$base_url/api/v1/dji/cloud/status"
echo

echo "FH2-Status:"
curl --fail --silent "$base_url/api/v1/fh2/status"
echo

echo "FH2-V2-Routen:"
openapi_json="$(curl --fail --silent "$base_url/api/openapi.json")"
for route in \
  "/api/v1/fh2/devices" \
  "/api/v1/fh2/hms" \
  "/api/v1/fh2/waylines" \
  "/api/v1/fh2/flight-tasks" \
  "/api/v1/cameras/status" \
  "/api/v1/cameras/paths" \
  "/api/v1/cameras/telemetry" \
  "/api/v1/dji/cloud/status" \
  "/api/v1/dji/cloud/bootstrap"
do
  if ! grep -Fq "$route" <<<"$openapi_json"; then
    echo "FH2-V2-Route fehlt im OpenAPI-Schema: $route" >&2
    exit 1
  fi
  echo "  $route: OK"
done

echo "MQTT-Authentifizierungstest:"
if podman exec m4-mqtt mosquitto_pub -h 127.0.0.1 -p 1883 -t m4/health -m anonymous-must-fail >/dev/null 2>&1; then
  echo "Fehler: anonymer MQTT-Zugriff wurde akzeptiert." >&2
  exit 1
fi
podman exec m4-mqtt sh -c 'mosquitto_pub -h 127.0.0.1 -p 1883 -u "$MQTT_HEALTH_USERNAME" -P "$MQTT_HEALTH_PASSWORD" -t m4/health -m authenticated'
echo "Anonym abgewiesen, authentifiziert akzeptiert: OK"

marker="quadlet-verify-$(date +%s)-$"

echo "HTTP-Persistenztest:"
curl --fail --silent   -H 'Content-Type: application/json'   -d "{\"source\":\"quadlet-verify-http\",\"topic\":\"verify/http\",\"payload\":{\"marker\":\"$marker-http\"}}"   "$base_url/api/v1/events"
echo

http_events="$(curl --fail --silent "$base_url/api/v1/events?limit=100")"
if ! grep -Fq "$marker-http" <<<"$http_events"; then
  echo "HTTP-Testevent wurde nicht in PostgreSQL gefunden." >&2
  exit 1
fi
echo "HTTP -> PostgreSQL: OK"

echo "MQTT-Persistenztest:"
podman exec m4-mqtt sh -c 'mosquitto_pub -h 127.0.0.1 -p 1883 -u "$MQTT_HEALTH_USERNAME" -P "$MQTT_HEALTH_PASSWORD" -q 1 -t m4/fh2/verify -m '"'"'{"marker":"'"$marker-mqtt"'"}'"'"''

attempt=0
while true; do
  mqtt_events="$(curl --fail --silent "$base_url/api/v1/events?limit=100")"
  if grep -Fq "$marker-mqtt" <<<"$mqtt_events"; then
    break
  fi

  attempt=$((attempt + 1))
  if (( attempt >= 15 )); then
    echo "MQTT-Testevent wurde nicht über den Integration Worker persistiert." >&2
    journalctl --user -u integration-worker.service -u mqtt.service -n 100 --no-pager
    exit 1
  fi
  sleep 1
done
echo "MQTT -> Integration Worker -> PostgreSQL: OK"

echo
podman ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
echo
echo "M4-Cloud Quadlet-Abnahme erfolgreich."
