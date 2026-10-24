"""
Platform Operations API views.

All endpoints require active platform superuser authority.
No X-School-ID header is required — these are cross-tenant super-admin operations.

Routes (registered in platform_ops/urls.py):
  POST /api/platform/schools                 — create school + queue provisioning
  GET  /api/platform/schools/list            — paginated list of all tenants
  GET  /api/platform/provisioning/<job_id>   — provisioning job status
"""
from __future__ import annotations

import logging
import uuid

from rest_framework.decorators import api_view, permission_classes
from core.permissions import IsPlatformOperator
from rest_framework.request import Request
from rest_framework.response import Response


logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# POST /api/platform/schools
# ─────────────────────────────────────────────────────────────────────────────

@api_view(["POST"])
@permission_classes([IsPlatformOperator])
def platform_create_school(request: Request) -> Response:
    """
    Create a new school tenant and queue its provisioning job.

    Required body fields:
      name            str — display name for the school
      slug            str — URL-safe identifier (must be globally unique)
      idempotency_key str — caller-generated idempotency key (UUID recommended)

    Optional body fields:
      domain           str — custom domain (default "")
      plan_code        str — starter | growth | enterprise (default "starter")
      timezone         str — IANA timezone string (default "America/New_York")
      payment_provider str — manual | none (default "none")

    Returns:
      201 on first creation, 200 on idempotent repeat.
      {"job_id": "...", "school_id": "...", "state": "queued", "idempotent": bool}
    """
    data = request.data

    name = (data.get("name") or "").strip()
    slug = (data.get("slug") or "").strip()
    idempotency_key = (data.get("idempotency_key") or "").strip()

    # ── Validate required fields and payment mode before any DB write ─────────
    errors: dict[str, str] = {}
    if not name:
        errors["name"] = "This field is required."
    if not slug:
        errors["slug"] = "This field is required."
    if not idempotency_key:
        errors["idempotency_key"] = "This field is required."

    from platform_ops.provisioning import normalize_payment_provider  # noqa: PLC0415

    try:
        payment_provider = normalize_payment_provider(data.get("payment_provider", "none"))
    except ValueError as exc:
        errors["payment_provider"] = str(exc)

    if errors:
        return Response({"errors": errors}, status=400)

    # ── Check idempotency before any DB write ────────────────────────────────
    from platform_ops.models import ProvisioningJob  # noqa: PLC0415

    existing = ProvisioningJob.objects.filter(idempotency_key=idempotency_key).first()
    is_idempotent = existing is not None

    if existing is None:
        from platform_ops.provisioning import create_school_and_queue_provisioning  # noqa: PLC0415

        actor_id = getattr(request.user, "id", None)
        try:
            actor_uuid = uuid.UUID(str(actor_id)) if actor_id else None
        except (ValueError, TypeError):
            actor_uuid = None

        try:
            job = create_school_and_queue_provisioning(
                name=name,
                slug=slug,
                domain=data.get("domain", ""),
                plan_code=data.get("plan_code", "starter"),
                timezone_str=data.get("timezone", "America/New_York"),
                payment_provider=payment_provider,
                idempotency_key=idempotency_key,
                actor_user_id=actor_uuid,
                request=request._request,
            )
        except Exception:
            logger.exception("platform_create_school failed")
            return Response({"error": "Unable to create school at this time."}, status=500)
    else:
        job = existing

    status_code = 200 if is_idempotent else 201
    return Response(
        {
            "job_id": str(job.id),
            "school_id": str(job.school_id),
            "state": job.state,
            "idempotent": is_idempotent,
        },
        status=status_code,
    )


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/platform/schools/list
# ─────────────────────────────────────────────────────────────────────────────

@api_view(["GET"])
@permission_classes([IsPlatformOperator])
def platform_list_schools(request: Request) -> Response:
    """
    Return a paginated list of all school tenants with TenantProfile data.

    Query params:
      page     int — 1-based page number (default 1)
      per_page int — results per page (default 50, max 200)
      status   str — filter by TenantProfile.status (optional)
    """
    from tenants.models import TenantProfile  # noqa: PLC0415

    try:
        page = max(1, int(request.query_params.get("page", 1)))
        per_page = min(200, max(1, int(request.query_params.get("per_page", 50))))
    except (ValueError, TypeError):
        return Response({"error": "Invalid pagination parameters."}, status=400)

    qs = TenantProfile.objects.select_related("school").order_by("slug")

    status_filter = request.query_params.get("status", "").strip()
    if status_filter:
        qs = qs.filter(status=status_filter)

    total = qs.count()
    offset = (page - 1) * per_page
    profiles = qs[offset : offset + per_page]

    results = [
        {
            "school_id": str(p.school_id),
            "school_name": p.school.name,
            "slug": p.slug,
            "plan_code": p.plan_code,
            "status": p.status,
            "domain": p.domain,
            "timezone": p.timezone,
            "payment_provider": p.payment_provider,
            "created_at": p.created_at.isoformat(),
        }
        for p in profiles
    ]

    return Response(
        {
            "total": total,
            "page": page,
            "per_page": per_page,
            "results": results,
        }
    )


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/platform/provisioning/<job_id>
# ─────────────────────────────────────────────────────────────────────────────

@api_view(["GET"])
@permission_classes([IsPlatformOperator])
def platform_provisioning_status(request: Request, job_id: uuid.UUID) -> Response:
    """
    Return the current status of a provisioning job.

    Path param: job_id (UUID)
    """
    from platform_ops.models import ProvisioningJob  # noqa: PLC0415

    try:
        job = ProvisioningJob.objects.select_related("school").get(id=job_id)
    except ProvisioningJob.DoesNotExist:
        return Response({"error": "Provisioning job not found."}, status=404)

    return Response(
        {
            "job_id": str(job.id),
            "school_id": str(job.school_id),
            "school_name": job.school.name,
            "state": job.state,
            "progress": job.progress,
            "error": "Provisioning failed. Check server logs." if job.error else None,
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "finished_at": job.finished_at.isoformat() if job.finished_at else None,
            "created_at": job.created_at.isoformat(),
            "updated_at": job.updated_at.isoformat(),
        }
    )


@api_view(["GET"])
@permission_classes([IsPlatformOperator])
def platform_overview(request: Request) -> Response:
    """Return platform-owned operational facts from the current database.

    This is not a tenant dashboard, a customer-count attestation, a company
    general ledger, or a payment gateway health check. Counts may include
    synthetic records in non-production environments. Never return audit
    payloads, provisioning error strings, or any family/student data.
    """
    from datetime import timedelta

    from django.db.models import Count
    from django.utils import timezone

    from platform_ops.models import AuditEvent, ProvisioningJob
    from tenants.models import TenantProfile

    now = timezone.now()
    schools_by_status = {
        state: 0 for state, _label in TenantProfile.STATUS_CHOICES
    }
    for entry in TenantProfile.objects.values("status").annotate(
        total=Count("pk")
    ):
        schools_by_status[entry["status"]] = entry["total"]

    jobs_by_state = {
        state: 0 for state, _label in ProvisioningJob.STATE_CHOICES
    }
    for entry in ProvisioningJob.objects.values("state").annotate(
        total=Count("pk")
    ):
        jobs_by_state[entry["state"]] = entry["total"]

    recent_jobs = [
        {
            "job_id": str(job.id),
            "school_id": str(job.school_id),
            "school_name": job.school.name,
            "state": job.state,
            "progress": job.progress,
            "created_at": job.created_at.isoformat(),
        }
        for job in ProvisioningJob.objects.select_related("school")
        .order_by("-created_at", "-pk")[:10]
    ]

    return Response(
        {
            "schools": {
                "total": sum(schools_by_status.values()),
                "by_status": schools_by_status,
            },
            "provisioning": {
                "by_state": jobs_by_state,
                "recent_jobs": recent_jobs,
            },
            "audit": {
                "events_last_7_days": AuditEvent.objects.filter(
                    created_at__gte=now - timedelta(days=7)
                ).count(),
            },
            "company_finance": {
                "data_state": "not_configured",
                "reason": (
                    "CROWN corporate revenue, invoices, receivables, refunds, "
                    "and cash collections require an authoritative, reconciled "
                    "company ledger. School tuition is not company revenue."
                ),
            },
            "external_payments": {
                "provisioning_policy": "disabled",
                "allowed_modes": ["none", "manual"],
            },
            "meta": {
                "data_source": "live_db",
                "scope": "current_database",
                "as_of": now.isoformat(),
                "financial_data_source": "not_configured",
            },
        }
    )
