#!/usr/bin/env bash
set -euo pipefail

cd /home/site/wwwroot/backend

echo "== Crown startup: migrate =="
python manage.py migrate --noinput

# Optional: only run when explicitly enabled
if [ "${CROWN_RUN_BOOTSTRAP:-0}" = "1" ]; then
  echo "== Crown startup: bootstrap demo data =="
  python manage.py golden_path_bootstrap
fi

echo "== Crown startup: start gunicorn =="
exec gunicorn crown_api.wsgi:application --bind 0.0.0.0:8000 --workers 2 --timeout 120
