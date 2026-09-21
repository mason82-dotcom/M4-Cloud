#!/usr/bin/env sh
set -eu

if [ ! -f .env ]; then
  echo "Fehlt: .env" >&2
  exit 2
fi

command -v docker >/dev/null 2>&1 || { echo "Fehlt: docker" >&2; exit 2; }
command -v openssl >/dev/null 2>&1 || { echo "Fehlt: openssl" >&2; exit 2; }

set -a
. ./.env
set +a

cert="${MQTT_TLS_CERT_FILE:-./secrets/mqtt-tls/server.crt}"
key="${MQTT_TLS_KEY_FILE:-./secrets/mqtt-tls/server.key}"
host="${MQTT_PUBLIC_HOST:-}"

[ -n "$host" ] || { echo "MQTT_PUBLIC_HOST fehlt." >&2; exit 2; }
[ -r "$cert" ] || { echo "Zertifikat nicht lesbar: $cert" >&2; exit 2; }
[ -r "$key" ] || { echo "Private Key nicht lesbar: $key" >&2; exit 2; }

openssl x509 -in "$cert" -noout -subject -issuer -dates
openssl x509 -in "$cert" -checkend 86400 -noout
openssl pkey -in "$key" -noout >/dev/null

cert_pub="$(openssl x509 -in "$cert" -pubkey -noout)"
key_pub="$(openssl pkey -in "$key" -pubout)"
[ "$cert_pub" = "$key_pub" ] || { echo "Zertifikat und Private Key passen nicht zusammen." >&2; exit 1; }

if openssl x509 -help 2>&1 | grep -q -- "-checkhost"; then
  openssl x509 -in "$cert" -checkhost "$host" -noout
fi

docker compose -f docker-compose.yml -f docker-compose.tls.yml config >/dev/null

echo "MQTT-TLS-Konfiguration statisch geprüft. Es wurde kein Stack gestartet."
