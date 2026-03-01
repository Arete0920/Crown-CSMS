from django.http import JsonResponse
from django.conf import settings
from django.db import connection
import os
import socket
from datetime import datetime, timezone

# --- CROWN_ENV_BOOL_HELPER ---

def _crown_env_true(name: str, default: bool = False) -> bool:
    v = os.getenv(name)
    if v is None:
        return default
    v = str(v).strip().lower()
    return v in ("1","true","t","yes","y","on")



def health(request):
    """
    Minimal health check with deploy determinism proof.
    Returns: build_sha (40-char), env, build_time_utc, version, db status
    """
    build_sha = os.getenv("BUILD_SHA") or os.getenv("GITHUB_SHA") or "local-dev"
    prod_deploy_tag = os.getenv("PROD_DEPLOY_TAG", "")
    env_name = os.getenv("CROWN_ENV", "dev")
    build_time = datetime.now(timezone.utc).isoformat()
    version = os.getenv("APP_VERSION", "crown-0.3.0")
    deploy_run_id = os.getenv("DEPLOY_RUN_ID", "")
    deploy_workflow = os.getenv("DEPLOY_WORKFLOW", "")
    
    # Quick DB check
    db_status = "ok"
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except Exception:
        db_status = "unreachable"
    
    return JsonResponse({
        "ok": True,
        "status": "ok",
        "demo_mode": _crown_env_true('CROWN_DEMO_MODE', default=False),
        "build_sha": build_sha,
        "prod_deploy_tag": prod_deploy_tag,
        "env": env_name,
        "build_time_utc": build_time,
        "version": version,
        "db": db_status,
        "deploy_run_id": deploy_run_id,
        "deploy_workflow": deploy_workflow,
    })


def health_version(request):
    """Detailed version info for deployment verification."""
    build_sha = os.getenv("BUILD_SHA") or os.getenv("GITHUB_SHA") or "local-dev"
    build_time = os.getenv("BUILD_TIME") or "unknown"
    return JsonResponse({
        "build_sha": build_sha,
        "build_time": build_time,
        "env": os.environ.get("CROWN_ENV", "unknown"),
        "debug": getattr(settings, "DEBUG", False),
    })


def system_health(request):
    """
    Production-grade health endpoint.

    Contract:
    - Always returns JSON
    - 200 if DB is reachable
    - 503 if DB is not reachable
    - Includes BUILD_SHA for deployment proof (falls back to 'local-dev')

    Notes:
    - Safe for load balancers / uptime monitors
    - Uses a trivial SELECT 1 to confirm DB query execution
    """
    from django.utils import timezone
    
    ts = timezone.now().isoformat()
    build_sha = os.environ.get("BUILD_SHA", "local-dev")
    hostname = socket.gethostname()

    db_ok = False
    db_error = None

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1;")
            cursor.fetchone()
        db_ok = True
    except Exception as e:
        db_error = f"{type(e).__name__}: {e}"

    payload = {
        "ok": db_ok,
        "status": "healthy" if db_ok else "unhealthy",
        "ts": ts,
        "build_sha": build_sha,
        "host": hostname,
        "database": {
            "connected": db_ok,
            "error": db_error,
        },
    }

    return JsonResponse(payload, status=200 if db_ok else 503)

