#!/usr/bin/env bash
set -euo pipefail

cd /home/site/wwwroot/backend

# Schema changes run only in the controlled migration stage.
# Startup verifies that the expected schema is already present.
echo "== Crown startup: verify schema is current =="
python manage.py migrate --check

# Ensure CI smoke user exists when credentials are configured (idempotent)
if [ -n "${CI_SMOKE_USERNAME:-}" ]; then
  echo "== Crown startup: ensure CI smoke user =="
  python manage.py ensure_ci_user
fi

# Optional: only run when explicitly enabled
if [ "${CROWN_RUN_BOOTSTRAP:-0}" = "1" ]; then
  echo "== Crown startup: bootstrap demo data =="
  python manage.py golden_path_bootstrap
fi

echo "== Crown startup: start gunicorn =="
exec gunicorn crown_api.wsgi:application --bind 0.0.0.0:8000 --workers 2 --timeout 120
