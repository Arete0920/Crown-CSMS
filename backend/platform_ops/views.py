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

def _matches_onboarding_request(job, details: dict, actor_id: uuid.UUID) -> bool:
    """Fail closed when an idempotency key is replayed with different intent.

    A matching key must belong to the same principal and original school
    details. Never return another operator's school/job metadata on conflict.
    """
    from tenants.models import TenantProfile

    if job.created_by_user_id != actor_id:
        return False
    try:
        profile = job.school.tenant_profile
    except TenantProfile.DoesNotExist:
        return False
    return (
        job.school.name == details["name"]
        and profile.slug == details["slug"]
        and profile.domain == details["domain"]
        and profile.plan_code == details["plan_code"]
        and profile.timezone == details["timezone"]
        and profile.payment_provider == details["payment_provider"]
    )


@api_view(["POST"])
@permission_classes([IsPlatformOperator])
def platform_create_school(request: Request) -> Response:
    """Create one validated school and atomically queue its audited job.

    A repeated key only succeeds for the original operator and same exact
    normalized request. School creation does not execute its queued job.
    """
    from django.db import IntegrityError
    from platform_ops.models import ProvisioningJob
    from platform_ops.provisioning import create_school_and_queue_provisioning
    from platform_ops.school_create_validation import PlatformSchoolCreateSerializer

    serializer = PlatformSchoolCreateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({"errors": serializer.errors}, status=400)
    details = serializer.validated_data
    key = details["idempotency_key"]

    try:
        actor_id = uuid.UUID(str(request.user.pk))
    except (ValueError, TypeError, AttributeError):
        return Response({"error": "Platform operator identity unavailable."}, status=403)

    def find_existing():
        return (
            ProvisioningJob.objects.select_related("school", "school__tenant_profile")
            .filter(idempotency_key=key)
            .first()
        )

    job = find_existing()
    is_idempotent = job is not None
    if job is None:
        try:
            job, created = create_school_and_queue_provisioning(
                name=details["name"],
                slug=details["slug"],
                domain=details["domain"],
                plan_code=details["plan_code"],
                timezone_str=details["timezone"],
                payment_provider=details["payment_provider"],
                idempotency_key=key,
                actor_user_id=actor_id,
                request=request._request,
                return_created=True,
            )
            is_idempotent = not created
        except IntegrityError:
            # The atomic service rolls back a duplicate slug or racing key.
            # Re-query only after its transaction has ended.
            job = find_existing()
            if job is None:
                return Response(
                    {"error": "School identifier already exists."},
                    status=409,
                )
            is_idempotent = True
        except Exception:
            logger.exception("Platform school intake failed")
            return Response(
                {"error": "Unable to create school at this time."},
                status=500,
            )

    if not _matches_onboarding_request(job, details, actor_id):
        return Response(
            {"error": "Onboarding key already used for a different request."},
            status=409,
        )

    return Response(
        {
            "job_id": str(job.id),
            "school_id": str(job.school_id),
            "state": job.state,
            "idempotent": is_idempotent,
        },
        status=200 if is_idempotent else 201,
    )


# ─────────────────────────────────────────────────────────────────────────────
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

    from django.db.models import Count, Q
    from django.utils import timezone

    from platform_ops.models import AuditEvent, ProvisioningJob
    from support.models import SLA_HOURS, SupportTicket
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

    # One aggregate query supplies an owner-only, PII-free support pulse.
    # Match the school's existing SLA thresholds; this does not certify that
    # Celery, on-call notification or external message delivery is operating.
    overdue_open = Q(pk__in=[])
    for priority, hours in SLA_HOURS.items():
        overdue_open |= Q(
            status=SupportTicket.STATUS_OPEN,
            priority=priority,
            created_at__lte=now - timedelta(hours=hours),
        )
    ticket_counts = SupportTicket.objects.aggregate(
        open=Count("pk", filter=Q(status=SupportTicket.STATUS_OPEN)),
        escalated=Count("pk", filter=Q(status=SupportTicket.STATUS_ESCALATED)),
        critical_unresolved=Count(
            "pk", filter=Q(
                status__in=(SupportTicket.STATUS_OPEN, SupportTicket.STATUS_ESCALATED),
                priority="critical",
            ),
        ),
        overdue_open=Count("pk", filter=overdue_open),
    )

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
            "support": {
                "data_state": "available",
                "scope": "current_database",
                "unresolved": ticket_counts["open"] + ticket_counts["escalated"],
                "open": ticket_counts["open"],
                "escalated": ticket_counts["escalated"],
                "critical_unresolved": ticket_counts["critical_unresolved"],
                "overdue_open": ticket_counts["overdue_open"],
                "alert_delivery": "not_certified",
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
