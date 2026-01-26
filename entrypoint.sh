#!/usr/bin/env bash
set -euo pipefail

cd /app/backend

echo "ENTRYPOINT_SEES: RUN_MIGRATE=${RUN_MIGRATE:-<unset>}"
echo "ENTRYPOINT_SEES: RUN_DEV_BOOTSTRAP=${RUN_DEV_BOOTSTRAP:-<unset>}"
echo "ENTRYPOINT_SEES: RUN_GOLDEN_PATH_BOOTSTRAP=${RUN_GOLDEN_PATH_BOOTSTRAP:-<unset>}"
echo "ENTRYPOINT_SEES: PORT=${PORT:-<unset>} WEBSITES_PORT=${WEBSITES_PORT:-<unset>}"

# Optional, idempotent startup tasks (safe for dev/CI).
if [[ "${RUN_MIGRATE:-0}" == "1" ]]; then
  python manage.py migrate --noinput
fi

if [[ "${RUN_DEV_BOOTSTRAP:-0}" == "1" ]]; then
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
