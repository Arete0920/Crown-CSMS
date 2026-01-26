#!/usr/bin/env bash
set -euo pipefail

cd /app/backend

# Optional, idempotent startup tasks (safe for dev/CI).
if [[ "${RUN_MIGRATE:-1}" == "1" ]]; then
  python manage.py migrate --noinput
fi

if [[ "${RUN_DEV_BOOTSTRAP:-1}" == "1" ]]; then
  python manage.py dev_bootstrap
fi

if [[ "${RUN_GOLDEN_PATH_BOOTSTRAP:-0}" == "1" ]]; then
  echo "=== GOLDEN_PATH_BOOTSTRAP_BEGIN ==="
  python manage.py golden_path_bootstrap || true
  echo "=== GOLDEN_PATH_BOOTSTRAP_END ==="
fi

exec gunicorn crown_api.wsgi:application \
  --bind "0.0.0.0:${PORT:-8000}" \
  --workers 2 \
  --threads 4 \
  --timeout 60
