#!/usr/bin/env sh
set -eu

repo_root="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
cd "$repo_root"

python_bin="${PYTHON:-$repo_root/.venv/bin/python}"

if [ ! -x "$python_bin" ]; then
  echo "Python-Venv fehlt: $python_bin" >&2
  echo "Im Dev Container zuerst .devcontainer/post-create.sh ausführen." >&2
  exit 2
fi

echo "Ruff..."
(
  cd services/control-api
  "$python_bin" -m ruff check app tests
)

echo
echo "Pytest..."
(
  cd services/control-api
  "$python_bin" -m pytest -q
)

echo
echo "M4-Cloud Entwicklerprüfung erfolgreich."
