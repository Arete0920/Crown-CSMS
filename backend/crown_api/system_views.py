from __future__ import annotations

import io
from django.conf import settings
from django.core.management import call_command
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser

from core.models_seed import SeedRun


class SeedStatusView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        runs = SeedRun.objects.all()[:10]
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

    try:
        # 1) migrate (keyword options only)
        call_command(
            "migrate",
            interactive=False,
            verbosity=verbosity_int,
            stdout=out_migrate,
            stderr=out_migrate,
        )

        # 2) reseed (keyword options only)
        call_command(
            "golden_path_bootstrap",
            force=True,
            school_id=str(school_id),
            verbosity=verbosity_int,
            stdout=out_seed,
            stderr=out_seed,
        )
        
        # 3) seed academics (courses, sections, enrollments)
        call_command(
            "seed_academics_demo",
            school_id=str(school_id),
            verbosity=verbosity_int,
            stdout=out_academics,
            stderr=out_academics,
        )
        
        # 4) seed demonstration category weights
        call_command(
            "seed_category_weights",
            school_id=str(school_id),
            verbosity=verbosity_int,
            stdout=out_categories,
            stderr=out_categories,
        )

    except Exception as e:
        # Return JSON error instead of Django HTML 500 page
        return JsonResponse(
            {
                "ok": False,
                "error_type": e.__class__.__name__,
                "error": str(e),
                "migrate_tail": out_migrate.getvalue()[-2000:],
                "seed_tail": out_seed.getvalue()[-2000:],
                "academics_tail": out_academics.getvalue()[-2000:],
                "categories_tail": out_categories.getvalue()[-2000:],
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
        },
        status=200,
    )
