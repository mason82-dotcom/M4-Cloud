#!/bin/sh
set -eu

: "${MQTT_WORKER_USERNAME:=m4-worker}"
: "${MQTT_WORKER_PASSWORD:?MQTT_WORKER_PASSWORD is required}"
: "${MQTT_HEALTH_USERNAME:=m4-health}"
: "${MQTT_HEALTH_PASSWORD:?MQTT_HEALTH_PASSWORD is required}"
: "${DJI_CLOUD_API_ENABLED:=false}"
: "${DJI_MQTT_USERNAME:=dji-pilot}"

runtime_dir=/mosquitto/runtime
password_file="$runtime_dir/passwords"
acl_file="$runtime_dir/acl"

mkdir -p "$runtime_dir"
umask 077

mosquitto_passwd -b -c "$password_file" "$MQTT_WORKER_USERNAME" "$MQTT_WORKER_PASSWORD"
mosquitto_passwd -b "$password_file" "$MQTT_HEALTH_USERNAME" "$MQTT_HEALTH_PASSWORD"

cat >"$acl_file" <<EOF
user $MQTT_WORKER_USERNAME
topic read m4/fh2/#
topic read thing/product/+/osd
topic read thing/product/+/state
topic read thing/product/+/services_reply
topic read thing/product/+/events
topic read thing/product/+/requests
topic read thing/product/+/property/set_reply
topic read thing/product/+/drc/up
topic read sys/product/+/status

user $MQTT_HEALTH_USERNAME
topic readwrite m4/health
topic write m4/fh2/verify
topic write m4/fh2/ci
EOF

case "$(printf '%s' "$DJI_CLOUD_API_ENABLED" | tr '[:upper:]' '[:lower:]')" in
  1|true|yes|on)
    : "${DJI_MQTT_PASSWORD:?DJI_MQTT_PASSWORD is required when DJI Cloud API is enabled}"
    mosquitto_passwd -b "$password_file" "$DJI_MQTT_USERNAME" "$DJI_MQTT_PASSWORD"
    cat >>"$acl_file" <<EOF

user $DJI_MQTT_USERNAME
topic write thing/product/+/osd
topic write thing/product/+/state
topic write thing/product/+/services_reply
topic write thing/product/+/events
topic write thing/product/+/requests
topic write thing/product/+/property/set_reply
topic write sys/product/+/status
topic read thing/product/+/services
topic read thing/product/+/events_reply
topic read thing/product/+/requests_reply
topic read thing/product/+/property/set
topic read sys/product/+/status_reply
EOF
    ;;
esac

chown -R mosquitto:mosquitto "$runtime_dir"
chmod 0640 "$password_file" "$acl_file"

exec mosquitto -c /mosquitto/config/mosquitto.conf
