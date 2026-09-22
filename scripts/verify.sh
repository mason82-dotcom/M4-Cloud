#!/usr/bin/env sh
set -eu

if [ ! -f .env ]; then
  echo "Fehlt: .env (cp .env.example .env und Secrets setzen)" >&2
  exit 2
fi

command -v docker >/dev/null 2>&1 || {
  echo "Fehlt: docker" >&2
  exit 2
}
command -v curl >/dev/null 2>&1 || {
  echo "Fehlt: curl" >&2
  exit 2
}

echo "Bootstrap-Token prüfen..."
DJI_BOOTSTRAP_TOKEN_VALUE="$(sed -n 's/^DJI_BOOTSTRAP_TOKEN=//p' .env | tail -n 1)"
if [ -z "$DJI_BOOTSTRAP_TOKEN_VALUE" ] || [ "$DJI_BOOTSTRAP_TOKEN_VALUE" = "change-me-bootstrap" ]; then
  echo "DJI_BOOTSTRAP_TOKEN muss in .env gesetzt werden." >&2
  exit 2
fi

echo "Compose-Konfiguration prüfen..."
docker compose config >/dev/null

echo "Images bauen..."
docker compose build

echo "Stack starten..."
docker compose up -d

echo "Auf Readiness warten..."
i=0
until curl --fail --silent "http://127.0.0.1:${M4_PORT:-8080}/ready" >/tmp/m4-ready.json 2>/dev/null; do
  i=$((i + 1))
  if [ "$i" -ge 60 ]; then
    cat /tmp/m4-ready.json 2>/dev/null || true
    docker compose ps
    docker compose logs --no-color --tail=200
    exit 1
  fi
  sleep 2
done
cat /tmp/m4-ready.json
echo

echo "Basis-APIs prüfen..."
curl --fail --silent "http://127.0.0.1:${M4_PORT:-8080}/health"
echo
curl --fail --silent "http://127.0.0.1:${M4_PORT:-8080}/api/v1/system"
echo
if curl --fail --silent \
  -H "X-M4-Bootstrap-Token: wrong-token" \
  "http://127.0.0.1:${M4_PORT:-8080}/api/v1/cloud/bootstrap" >/dev/null 2>&1; then
  echo "Bootstrap akzeptiert einen falschen Token." >&2
  exit 1
fi
curl --fail --silent \
  -H "X-M4-Bootstrap-Token: $DJI_BOOTSTRAP_TOKEN_VALUE" \
  "http://127.0.0.1:${M4_PORT:-8080}/api/v1/cloud/bootstrap"
echo
curl --fail --silent "http://127.0.0.1:${M4_PORT:-8080}/api/v1/fh2/status"
echo
curl --fail --silent "http://127.0.0.1:${M4_PORT:-8080}/api/v1/cameras/status"
echo

echo "MQTT-Rollen prüfen..."
echo "Anonymen MQTT-Zugriff ablehnen..."
if docker compose exec -T mqtt mosquitto_pub \
  -h 127.0.0.1 -p 1883 -q 1 -t m4/verify -m anonymous >/dev/null 2>&1; then
  echo "Anonymer MQTT-Zugriff wurde unerwartet akzeptiert." >&2
  exit 1
fi

docker compose exec -T mqtt sh -ec '
  mosquitto_pub -h 127.0.0.1 -p 1883 \
    -u "$MQTT_SERVICE_USERNAME" -P "$MQTT_SERVICE_PASSWORD" \
    -q 1 -t m4/verify -m "{\"ok\":true}"

  mosquitto_pub -h 127.0.0.1 -p 1883 \
    -u "$DJI_MQTT_USERNAME" -P "$DJI_MQTT_PASSWORD" \
    -q 1 -t thing/product/M4VERIFY/state -m "{\"ok\":true}"
'

echo
docker compose ps
echo
echo "M4-Cloud V2.0 Basisprüfung erfolgreich. Stack bleibt gestartet."
