#!/usr/bin/env sh
set -eu

python -m compileall -q services/control-api/app
python -m pytest -q services/control-api/tests
docker compose config >/dev/null

echo "M4-Cloud Basisprüfung erfolgreich."
