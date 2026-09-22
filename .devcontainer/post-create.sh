#!/usr/bin/env sh
set -eu

repo_root="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
cd "$repo_root"

if [ ! -x .venv/bin/python ]; then
  python -m venv .venv
fi

.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r services/control-api/requirements-dev.txt

echo
echo "M4-Cloud Dev Container ist bereit."
echo "Lokale Codeprüfung: ./scripts/dev-check.sh"
