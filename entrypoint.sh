#!/usr/bin/env bash
set -euo pipefail

cd /app/backend

echo "ENTRYPOINT_SEES: RUN_DEV_BOOTSTRAP=${RUN_DEV_BOOTSTRAP:-<unset>}"
echo "ENTRYPOINT_SEES: RUN_GOLDEN_PATH_BOOTSTRAP=${RUN_GOLDEN_PATH_BOOTSTRAP:-<unset>}"
echo "ENTRYPOINT_SEES: PORT=${PORT:-<unset>} WEBSITES_PORT=${WEBSITES_PORT:-<unset>}"

# Production schema mutation belongs exclusively to the controlled migration stage.
# Startup fails closed when the deployed code expects unapplied migrations.
echo "== entrypoint: verify schema is current =="
python manage.py migrate --check

# Reject development-only startup actions before any data mutation in production.
python - <<'PYGUARD'
import os
production = bool(os.getenv("WEBSITE_HOSTNAME")) or any(
    os.getenv(key, "").strip().lower() in {"prod", "production", "live"}
    for key in ("CROWN_ENV", "DJANGO_ENV", "ENVIRONMENT", "AZURE_ENVIRONMENT")
)
if production:
    blocked = []
    for key in ("SEED_DEMO", "RUN_DEV_BOOTSTRAP", "RUN_GOLDEN_PATH_BOOTSTRAP"):
        if os.getenv(key, "").strip().lower() in {"1", "true", "yes", "on"}:
            blocked.append(key)
    if os.getenv("CI_SMOKE_USERNAME"):
        blocked.append("CI_SMOKE_USERNAME")
    if blocked:
        raise SystemExit("Production startup rejects development bootstrap flags: " + ", ".join(blocked))
PYGUARD

# Ensure CI smoke user exists when credentials are configured (dev/CI only).
if [ -n "${CI_SMOKE_USERNAME:-}" ]; then
  python manage.py ensure_ci_user
fi

# Read credentials inside Python; never interpolate environment values into code.
# Credentials alone never authorize administrator creation or password rotation.
if [ -n "${DJANGO_SUPERUSER_PASSWORD:-}" ] && [ "${BOOTSTRAP_ADMIN:-false}" != "true" ]; then
  echo "ERROR: DJANGO_SUPERUSER_PASSWORD is set but BOOTSTRAP_ADMIN is not explicitly true." >&2
  exit 1
fi
if [ "${BOOTSTRAP_ADMIN:-false}" = "true" ]; then
  python manage.py bootstrap_runtime_admin
fi

# --- Demo seed (optional, safe to skip) ---
if [ "${SEED_DEMO:-false}" = "true" ]; then
  echo "== entrypoint: seed_demo =="
  python manage.py seed_demo || true
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
