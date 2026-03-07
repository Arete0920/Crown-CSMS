#!/usr/bin/env bash
set -euo pipefail

cd /app/backend

echo "ENTRYPOINT_SEES: RUN_MIGRATE=${RUN_MIGRATE:-<unset>}"
echo "ENTRYPOINT_SEES: RUN_DEV_BOOTSTRAP=${RUN_DEV_BOOTSTRAP:-<unset>}"
echo "ENTRYPOINT_SEES: RUN_GOLDEN_PATH_BOOTSTRAP=${RUN_GOLDEN_PATH_BOOTSTRAP:-<unset>}"
echo "ENTRYPOINT_SEES: PORT=${PORT:-<unset>} WEBSITES_PORT=${WEBSITES_PORT:-<unset>}"

# Always run migrations — safe, idempotent, required for schema consistency.
echo "== entrypoint: migrate =="
python manage.py migrate --noinput

# Ensure CI smoke user exists when credentials are configured (dev/CI only).
if [ -n "${CI_SMOKE_USERNAME:-}" ]; then
  echo "== entrypoint: ensure_ci_user =="
  python manage.py ensure_ci_user
fi

# --- Admin bootstrap (idempotent: create OR update password if exists) ---
# Activated by BOOTSTRAP_ADMIN=true OR legacy DJANGO_SUPERUSER_USERNAME+PASSWORD pair.
_su_user="${DJANGO_SUPERUSER_USERNAME:-admin}"
_su_email="${DJANGO_SUPERUSER_EMAIL:-admin@crown.demo}"
_su_pass="${DJANGO_SUPERUSER_PASSWORD:-}"
if [ "${BOOTSTRAP_ADMIN:-false}" = "true" ] || [ -n "${_su_pass}" ]; then
  echo "== entrypoint: bootstrap admin (user=${_su_user}) =="
  python manage.py shell -c "
from django.contrib.auth import get_user_model
U = get_user_model()
u, created = U.objects.get_or_create(username='${_su_user}', defaults={'email': '${_su_email}'})
if created:
    u.is_staff = True
    u.is_superuser = True
if '${_su_pass}':
    u.set_password('${_su_pass}')
u.save()
print('bootstrap_admin: created=' + str(created))
"
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
