from __future__ import annotations

import io
import logging
from django.conf import settings
from django.core.management import call_command
from django.db import connection
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser

from core.models_seed import SeedRun
from crown_api.tenant import CANONICAL_TENANT_ATTR


logger = logging.getLogger(__name__)


def _run_sql(cursor, sql: str, params=None):
    exec_fn = getattr(cursor, "execute")
    return exec_fn(sql, [] if params is None else params)


class SeedStatusView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        runs = SeedRun.objects.order_by("-created_at")[:10]
        return Response(
            {
                "runs": [
                    {
                        "created_at": r.created_at.isoformat(),
                        "env_name": r.env_name,
                        "build_sha": r.build_sha,
                        "school_id": str(r.school_id) if r.school_id else None,
                        "command": r.command,
                        "force": r.force,
                        "status": r.status,
                        "summary": r.summary_json,
                        "error": r.error_text,
                    }
                    for r in runs
                ]
            }
        )


def _get_ops_secret() -> str:
    return getattr(settings, "CROWN_OPS_SECRET", "") or getattr(settings, "OPS_SECRET", "") or ""


def _is_dev_env() -> bool:
    env = (getattr(settings, "CROWN_ENV", "") or getattr(settings, "DJANGO_ENV", "") or "").lower()
    return env in ("dev", "development")


@csrf_exempt
def demo_reset_view(request):
    """
    DEV-only ops endpoint.
    Runs: migrate --noinput AND golden_path_bootstrap --force --school-id <id>
    Protected by: X-Admin-Ops-Secret header matching CROWN_OPS_SECRET
    """
    if request.method not in ("POST",):
        return JsonResponse({"detail": "Method not allowed"}, status=405)

    if not _is_dev_env():
        return JsonResponse({"detail": "Not allowed outside dev"}, status=403)

    secret = _get_ops_secret()
    header = request.headers.get("X-Admin-Ops-Secret", "")
    if not secret or header != secret:
        return JsonResponse({"detail": "Forbidden"}, status=403)

    school_id = request.headers.get("X-School-Id") or request.GET.get("school_id") or ""
    if not school_id:
        return JsonResponse({"detail": "Missing school_id (send X-School-Id or ?school_id=...)"}, status=400)

    verbosity = request.GET.get("verbosity", "1")
    try:
        verbosity_int = int(verbosity)
    except Exception:
        verbosity_int = 1

    out_migrate = io.StringIO()
    out_seed = io.StringIO()
    out_academics = io.StringIO()
    out_categories = io.StringIO()
    out_gradebook = io.StringIO()

    try:
        call_command(
            "migrate",
            interactive=False,
            verbosity=verbosity_int,
            stdout=out_migrate,
            stderr=out_migrate,
        )
        call_command(
            "golden_path_bootstrap",
            force=True,
            school_id=str(school_id),
            verbosity=verbosity_int,
            stdout=out_seed,
            stderr=out_seed,
        )
        call_command(
            "seed_academics_demo",
            school_id=str(school_id),
            verbosity=verbosity_int,
            stdout=out_academics,
            stderr=out_academics,
        )
        call_command(
            "seed_category_weights",
            school_id=str(school_id),
            verbosity=verbosity_int,
            stdout=out_categories,
            stderr=out_categories,
        )
        call_command(
            "seed_gradebook_demo",
            school_id=str(school_id),
            per_section=12,
            seed=2026,
            wipe=True,
            verbosity=verbosity_int,
            stdout=out_gradebook,
            stderr=out_gradebook,
        )
    except Exception:
        logger.exception("demo_reset_view failed")
        return JsonResponse(
            {
                "ok": False,
                "error": "Demo reset failed.",
                "migrate_tail": out_migrate.getvalue()[-2000:],
                "seed_tail": out_seed.getvalue()[-2000:],
                "academics_tail": out_academics.getvalue()[-2000:],
                "categories_tail": out_categories.getvalue()[-2000:],
                "gradebook_tail": out_gradebook.getvalue()[-2000:],
            },
            status=500,
        )

    return JsonResponse(
        {
            "ok": True,
            "env": (getattr(settings, "CROWN_ENV", "") or getattr(settings, "DJANGO_ENV", "")),
            "school_id": school_id,
            "migrate_tail": out_migrate.getvalue()[-2000:],
            "seed_tail": out_seed.getvalue()[-2000:],
            "academics_tail": out_academics.getvalue()[-2000:],
            "categories_tail": out_categories.getvalue()[-2000:],
            "gradebook_tail": out_gradebook.getvalue()[-2000:],
        },
        status=200,
    )


@csrf_exempt
def diagnose_db_tables_view(request):
    """
    Temporary diagnostic endpoint to check DB table vs Django migration state.
    DEV-only. Requires OPS secret in header.
    """
    if not _is_dev_env():
        return JsonResponse({"error": "Only available in DEV"}, status=403)

    ops_secret = _get_ops_secret()
    if ops_secret and request.headers.get("X-Ops-Secret") != ops_secret:
        return JsonResponse({"error": "Invalid or missing X-Ops-Secret"}, status=401)

    try:
        with connection.cursor() as cursor:
            _run_sql(
                cursor,
                "SELECT to_regclass('public.financial_aid_financialaidapplication') AS fa_table;"
            )
            row = cursor.fetchone()
            fa_table = row[0] if row else None

            _run_sql(
                cursor,
                """
                SELECT app, name, applied
                FROM django_migrations
                WHERE app = 'financial_aid'
                ORDER BY applied DESC;
                """
            )
            migration_rows = cursor.fetchall()

            _run_sql(
                cursor,
                "SELECT current_database() AS db, inet_server_addr() AS server_ip, version();"
            )
            db_info = cursor.fetchone()

        has_table = fa_table is not None
        has_migrations = len(migration_rows) > 0

        if not has_table and has_migrations:
            diagnosis = "SCHEMA_DRIFT"
            message = "Migration ledger says 'applied' but table doesn't exist"
            fix = "DELETE FROM django_migrations WHERE app = 'financial_aid'; then re-migrate"
        elif has_table and not has_migrations:
            diagnosis = "PARTIAL_DRIFT"
            message = "Table exists but no migration ledger"
            fix = "Fake applied migrations or re-sync"
        elif not has_table and not has_migrations:
            diagnosis = "CLEAN"
            message = "No table, no migrations (expected for fresh DB)"
            fix = "None needed"
        else:
            diagnosis = "CONSISTENT"
            message = "Table exists and migrations recorded"
            fix = "None needed"

        return JsonResponse(
            {
                "ok": True,
                "table_exists": has_table,
                "table_name": fa_table,
                "migrations_count": len(migration_rows),
                "migrations": [
                    {"app": app, "name": name, "applied": str(applied)}
                    for app, name, applied in migration_rows
                ],
                "database": db_info[0],
                "server_ip": db_info[1],
                "pg_version": db_info[2][:80],
                "diagnosis": diagnosis,
                "message": message,
                "fix": fix,
            },
            status=200,
        )
    except Exception:
        logger.exception("diagnose_db_tables_view failed")
        return JsonResponse(
            {
                "ok": False,
                "error": "Unable to diagnose database tables.",
            },
            status=500,
        )


@csrf_exempt
def fix_schema_drift_view(request):
    """
    Temporary endpoint to fix financial_aid schema drift.
    DEV-only. Requires OPS secret in header.
    Executes: DELETE FROM django_migrations WHERE app = 'financial_aid', then re-migrate.
    """
    if not _is_dev_env():
        return JsonResponse({"error": "Only available in DEV"}, status=403)

    ops_secret = _get_ops_secret()
    if ops_secret and request.headers.get("X-Ops-Secret") != ops_secret:
        return JsonResponse({"error": "Invalid or missing X-Ops-Secret"}, status=401)

    try:
        out = io.StringIO()
        call_command("fix_schema_drift", stdout=out, stderr=out)
        return JsonResponse(
            {
                "ok": True,
                "message": "Schema drift fix completed successfully",
                "output": out.getvalue(),
            },
            status=200,
        )
    except Exception:
        logger.exception("fix_schema_drift_view failed")
        return JsonResponse(
            {
                "ok": False,
                "error": "Schema drift fix failed.",
            },
            status=500,
        )


from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def whoami(request):
    """Canonical proof endpoint for authenticated session, tenant, override, and build state."""
    user = request.user
    context = getattr(request, CANONICAL_TENANT_ATTR, None)

    user_data = {
        "id": str(getattr(user, "id", None)),
        "email": getattr(user, "email", None),
        "is_staff": getattr(user, "is_staff", False),
        "role": getattr(user, "role", None),
        "school_id": str(getattr(user, "school_id", None)) if getattr(user, "school_id", None) else None,
    }

    tenant_school_id = getattr(context, "school_id", None)
    tenant_data = {
        "resolved_school_id": str(tenant_school_id) if tenant_school_id else None,
        "resolution_source": getattr(context, "source", None),
        "header_present": bool(getattr(context, "header_present", False)),
    }

    override_school_id = tenant_school_id if bool(getattr(context, "override_authorized", False)) else None
    override_data = {
        "school_override_id": str(override_school_id) if override_school_id else None,
    }

    build_data = {
        "build_sha": settings.BUILD_SHA,
        "env": settings.CROWN_ENV or "unknown",
    }

    return JsonResponse({
        "ok": True,
        "user": user_data,
        "tenant": tenant_data,
        "override": override_data,
        "build": build_data,
    })
