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
    env_name = os.getenv("CROWN_ENV", "dev")
    build_time = datetime.now(timezone.utc).isoformat()
    version = os.getenv("APP_VERSION", "crown-0.3.0")
    
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
        "env": env_name,
        "build_time_utc": build_time,
        "version": version,
        "db": db_status,
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
    Production-grade health endpoint for uptime checks.
    Checks:
    - DB connectivity
    - Basic query execution
    - Host identity
    - BUILD_SHA
    """
    from django.utils import timezone as tz
    
    ts = tz.now().isoformat()
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
        db_error = str(e)

    status = "healthy" if db_ok else "unhealthy"

    return JsonResponse({
        "ok": db_ok,
        "status": status,
        "ts": ts,
        "build_sha": build_sha,
        "host": hostname,
        "database": {
            "connected": db_ok,
            "error": db_error
        }
    }, status=200 if db_ok else 503)

