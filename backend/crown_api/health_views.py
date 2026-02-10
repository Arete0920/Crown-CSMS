from django.http import JsonResponse
from django.conf import settings
from django.db import connection
import os
from datetime import datetime, timezone


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
