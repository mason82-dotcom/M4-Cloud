#!/usr/bin/env sh
set -eu

export POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-m4cloud-ci-password}"

cleanup() {
  docker compose down -v --remove-orphans >/dev/null 2>&1 || true
}
trap cleanup EXIT INT TERM

docker compose config --quiet
docker compose up -d --build

i=0
until curl --fail --silent http://127.0.0.1:"${M4_HTTP_PORT:-8080}"/ready >/dev/null; do
  i=$((i + 1))
  if [ "$i" -ge 30 ]; then
    docker compose ps
    docker compose logs --no-color
    exit 1
  fi
  sleep 2
done

curl --fail --silent http://127.0.0.1:"${M4_HTTP_PORT:-8080}"/health
curl --fail --silent http://127.0.0.1:"${M4_HTTP_PORT:-8080}"/api/v1/system/status
curl --fail --silent http://127.0.0.1:"${M4_HTTP_PORT:-8080}"/api/v1/fh2/status

printf '\nM4-Cloud V1 acceptance passed.\n'
