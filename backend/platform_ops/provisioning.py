"""
Platform provisioning engine.

Provides two public functions:

  create_school_and_queue_provisioning(...)
      Creates core.School + TenantProfile + SchoolSettings + ProvisioningJob
      atomically inside a transaction.  Idempotent: calling twice with the
      same idempotency_key returns the existing ProvisioningJob unchanged.

  run_provisioning_job(job, ...)
      Runs exactly one queued job under a row lock. Caller must separately
      authorize execution; creating a job never launches a worker.

Audit trail: every action is recorded via platform_ops.AuditEvent.
"""
from __future__ import annotations

import logging
import uuid
from typing import Optional

from django.db import transaction
from django.utils import timezone

logger = logging.getLogger(__name__)

SUPPORTED_PAYMENT_PROVIDERS = frozenset({"manual", "none"})
PAYMENT_PROCESSING_DISABLED_MESSAGE = (
    "External payment processing is disabled; use 'none' or 'manual'."
)
MAX_PROVISIONING_RETRIES = 2
PROVISIONING_RETRY_REASONS = frozenset({
    "transient_dependency",
    "corrected_configuration",
})


def normalize_payment_provider(value: str | None) -> str:
    """Return a permitted fail-closed payment mode or reject it."""

    provider = (value or "none").strip().lower()
    if provider not in SUPPORTED_PAYMENT_PROVIDERS:
        raise ValueError(PAYMENT_PROCESSING_DISABLED_MESSAGE)
    return provider


def audit(
    action: str,
    *,
    school_id: Optional[uuid.UUID],
    actor_user_id: Optional[uuid.UUID],
    payload: dict,
    request=None,
    resource_kind: str = "",
    resource_id: Optional[uuid.UUID] = None,
) -> None:
    """
    Record a platform-level AuditEvent.

    Required audit writes raise on failure, rolling back the surrounding transaction.
    """
    try:
        from platform_ops.models import AuditEvent  # noqa: PLC0415

        ip = None
        user_agent = ""
        request_id = ""
        if request is not None:
            ip = _get_client_ip(request)
            user_agent = request.META.get("HTTP_USER_AGENT", "")[:512]
            request_id = request.META.get("HTTP_X_REQUEST_ID", "")[:128]

        AuditEvent.objects.create(
            school_id=school_id,
            actor_user_id=actor_user_id,
            action=action,
            resource_kind=resource_kind,
            resource_id=resource_id,
            request_id=request_id,
            ip=ip,
            user_agent=user_agent,
            payload=payload,
        )
    except Exception as exc:  # pragma: no cover
        logger.error("Platform audit storage unavailable: action=%s", action)
        raise ProvisioningAuditError(
            "Required platform audit event could not be persisted."
        ) from exc


def _get_client_ip(request) -> Optional[str]:
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR") or None


@transaction.atomic
def create_school_and_queue_provisioning(
    *,
    name: str,
    slug: str,
    domain: str = "",
    plan_code: str = "starter",
    timezone_str: str = "America/New_York",
    payment_provider: str = "none",
    idempotency_key: str,
    actor_user_id: Optional[uuid.UUID] = None,
    request=None,
    return_created: bool = False,
) -> "ProvisioningJob | tuple[ProvisioningJob, bool]":
    """
    Idempotently create a school tenant and queue its provisioning job.

    With return_created=True, also report whether this call actually
    inserted the job, including after a concurrent idempotency replay.

    If a ProvisioningJob with idempotency_key already exists, returns it
    immediately without creating duplicate records.

    On first call:
      1. Creates core.School (or retrieves existing by name+slug)
      2. Creates TenantProfile (OneToOne extension)
      3. Creates SchoolSettings with empty defaults
      4. Creates ProvisioningJob in state=queued
      5. Records AuditEvent("school.created")
    """
    from platform_ops.models import ProvisioningJob  # noqa: PLC0415
    from tenants.models import SchoolSettings, TenantProfile  # noqa: PLC0415

    # ── Idempotency check ───────────────────────────────────────────────────
    existing = ProvisioningJob.objects.filter(idempotency_key=idempotency_key).first()
    if existing is not None:
        logger.info(
            "create_school_and_queue_provisioning: idempotency hit — returning existing job %s",
            existing.id,
        )
        return (existing, False) if return_created else existing

    payment_provider = normalize_payment_provider(payment_provider)

    # ── Create core.School ──────────────────────────────────────────────────
    from core.models import School  # noqa: PLC0415

    # Queued onboarding is not an authorized, active school session.
    school = School.objects.create(name=name, is_active=False)

    # ── Create TenantProfile ────────────────────────────────────────────────
    TenantProfile.objects.create(
        school=school,
        slug=slug,
        plan_code=plan_code,
        domain=domain,
        timezone=timezone_str,
        payment_provider=payment_provider,
        status="pending",
    )

    # ── Create SchoolSettings ───────────────────────────────────────────────
    SchoolSettings.objects.create(school=school)

    # ── Create ProvisioningJob ──────────────────────────────────────────────
    job = ProvisioningJob.objects.create(
        school=school,
        idempotency_key=idempotency_key,
        state=ProvisioningJob.STATE_QUEUED,
        progress=0,
        created_by_user_id=actor_user_id,
    )

    # Bind the queue entry and a minimal, non-PII audit record atomically.
    # A request's free-form headers and the school's name do not belong here.
    _record_provisioning_audit(
        "school.created",
        job_id=job.id,
        school_id=school.id,
        actor_user_id=actor_user_id,
        resource_kind="School",
        resource_id=school.id,
    )

    logger.info(
        "create_school_and_queue_provisioning: school=%s job=%s",
        school.id,
        job.id,
    )
    return (job, True) if return_created else job


class ProvisioningStateError(ValueError):
    """The stored provisioning state is unsafe to process or retry."""


class ProvisioningAuditError(RuntimeError):
    """Required provisioning audit evidence could not be persisted."""


def _record_provisioning_audit(
    action: str,
    *,
    job_id: uuid.UUID,
    school_id: uuid.UUID,
    actor_user_id: Optional[uuid.UUID],
    correlation_id: Optional[uuid.UUID] = None,
    resource_kind: str = "ProvisioningJob",
    resource_id: Optional[uuid.UUID] = None,
    retry_number: Optional[int] = None,
    reason_code: Optional[str] = None,
) -> None:
    """Persist correlated, non-sensitive evidence or roll back the mutation."""
    from platform_ops.models import AuditEvent

    payload = {"job_id": str(job_id)}
    if retry_number is not None:
        payload["retry_number"] = retry_number
    if reason_code is not None:
        payload["reason_code"] = reason_code
    try:
        AuditEvent.objects.create(
            action=action,
            school_id=school_id,
            actor_user_id=actor_user_id,
            resource_kind=resource_kind,
            resource_id=resource_id or job_id,
            request_id=str(correlation_id or job_id),
            payload=payload,
        )
    except Exception as exc:
        raise ProvisioningAuditError(
            "Required provisioning audit event could not be persisted."
        ) from exc


def _require_platform_operator(actor_user_id: Optional[uuid.UUID]) -> None:
    """Check schoolless operator authority at the service boundary."""
    from django.contrib.auth import get_user_model

    if not isinstance(actor_user_id, uuid.UUID) or not (
        get_user_model().objects.filter(
            pk=actor_user_id,
            is_active=True,
            is_superuser=True,
            school__isnull=True,
        ).exists()
    ):
        raise ProvisioningStateError(
            "An active, schoolless platform operator is required."
        )


def run_provisioning_job(
    job: "ProvisioningJob",
    *,
    actor_user_id: Optional[uuid.UUID] = None,
    request=None,
    correlation_id: Optional[uuid.UUID] = None,
) -> "ProvisioningJob":
    """Run exactly one queued job, using a database lock and durable audit.

    The transaction protects the job, tenant status and default settings as
    one operation. A second worker waits for the row lock, then sees the
    persisted terminal state. Failed/running jobs require separate recovery
    authorization; they are never retried implicitly. No external payment
    processing or external integration is activated.

    This short in-process routine does not publish intermediate progress:
    the running/progress values commit only when the transaction completes.
    The retained request parameter preserves the existing Python API but is
    deliberately not logged, avoiding request/credential leakage.
    """
    from platform_ops.models import ProvisioningJob
    from tenants.models import SchoolSettings, TenantProfile
    from core.models import School

    _require_platform_operator(actor_user_id)

    # Read the state from the database under the lock, never from a stale
    # Django object supplied by a queue consumer.
    try:
        with transaction.atomic():
            locked = ProvisioningJob.objects.select_for_update().get(pk=job.pk)
            if locked.state == ProvisioningJob.STATE_SUCCEEDED:
                return locked
            if locked.state != ProvisioningJob.STATE_QUEUED:
                raise ProvisioningStateError(
                    "Only queued provisioning jobs may execute."
                )

            profile = TenantProfile.objects.select_for_update().get(
                school_id=locked.school_id
            )
            if profile.status != "pending":
                raise ProvisioningStateError(
                    "A queued job requires a pending school tenant."
                )
            # Fail closed even if a legacy/manual write supplied an external
            # provider directly to the database.
            normalize_payment_provider(profile.payment_provider)

            _record_provisioning_audit(
                "provisioning.started",
                job_id=locked.pk,
                school_id=locked.school_id,
                actor_user_id=actor_user_id,
                correlation_id=correlation_id,
            )
            locked.state = ProvisioningJob.STATE_RUNNING
            locked.started_at = timezone.now()
            locked.progress = 10
            locked.save(
                update_fields=["state", "started_at", "progress", "updated_at"]
            )

            settings_obj, _ = SchoolSettings.objects.get_or_create(
                school_id=locked.school_id
            )
            if not settings_obj.modules:
                settings_obj.modules = {
                    "financial_aid": True,
                    "admissions": True,
                    "gradebook": True,
                    "attendance": True,
                    "billing": True,
                }
                settings_obj.save(update_fields=["modules", "updated_at"])

            profile.status = "active"
            profile.save(update_fields=["status", "updated_at"])

            # Keep core tenant access fail-closed until this transaction and
            # the required success audit both commit; a failure rolls back.
            School.objects.filter(pk=locked.school_id).update(is_active=True)

            _record_provisioning_audit(
                "provisioning.succeeded",
                job_id=locked.pk,
                school_id=locked.school_id,
                actor_user_id=actor_user_id,
                correlation_id=correlation_id,
            )
            locked.state = ProvisioningJob.STATE_SUCCEEDED
            locked.progress = 100
            locked.finished_at = timezone.now()
            locked.error = ""
            locked.save(
                update_fields=[
                    "state", "progress", "finished_at", "error", "updated_at"
                ]
            )
            return locked
    except (ProvisioningStateError, ProvisioningAuditError):
        # An invalid state or unavailable audit store must never trigger a
        # hidden retry or leave partially committed activation.
        raise
    except Exception as exc:
        # Do not store exception text, SQL, credentials or request payload in
        # the customer-facing job row or platform audit JSON.
        logger.error(
            "Provisioning job %s failed (%s)",
            job.pk,
            type(exc).__name__,
        )
        with transaction.atomic():
            failed = ProvisioningJob.objects.select_for_update().get(pk=job.pk)
            if failed.state != ProvisioningJob.STATE_QUEUED:
                raise ProvisioningStateError(
                    "Provisioning state changed during failure handling."
                ) from exc
            _record_provisioning_audit(
                "provisioning.failed",
                job_id=failed.pk,
                school_id=failed.school_id,
                actor_user_id=actor_user_id,
                correlation_id=correlation_id,
            )
            failed.state = ProvisioningJob.STATE_FAILED
            failed.error = "Provisioning failed. Review restricted server logs."
            failed.progress = 0
            failed.finished_at = timezone.now()
            failed.save(
                update_fields=[
                    "state", "error", "progress", "finished_at", "updated_at"
                ]
            )
            return failed


@transaction.atomic
def authorize_failed_provisioning_retry(
    job_id: uuid.UUID,
    *,
    actor_user_id: uuid.UUID,
    correlation_id: uuid.UUID,
    reason_code: str,
) -> "ProvisioningJob":
    """Requeue an audited failure, without executing it.

    A database row lock serializes competing recovery attempts. Every retry
    requires a distinct recorded failure, pending school state and an active
    schoolless operator. The two-attempt cap is derived from immutable audit
    records; no schema change or external payment action is involved.
    """
    from platform_ops.models import AuditEvent, ProvisioningJob
    from tenants.models import TenantProfile

    _require_platform_operator(actor_user_id)
    if not isinstance(correlation_id, uuid.UUID):
        raise ProvisioningStateError(
            "An approved change UUID is required for provisioning recovery."
        )
    if reason_code not in PROVISIONING_RETRY_REASONS:
        raise ProvisioningStateError("Unrecognized provisioning recovery reason.")

    locked = ProvisioningJob.objects.select_for_update().get(pk=job_id)
    if locked.state != ProvisioningJob.STATE_FAILED:
        raise ProvisioningStateError("Only failed provisioning jobs may be requeued.")
    profile = TenantProfile.objects.select_for_update().get(
        school_id=locked.school_id
    )
    if profile.status != "pending":
        raise ProvisioningStateError("Recovery requires a pending school.")
    try:
        normalize_payment_provider(profile.payment_provider)
    except ValueError as exc:
        raise ProvisioningStateError(
            "Unsupported payment configuration blocks recovery."
        ) from exc

    evidence = AuditEvent.objects.filter(
        resource_kind="ProvisioningJob",
        resource_id=locked.id,
    )
    failures = evidence.filter(
        action="provisioning.failed",
        actor_user_id__isnull=False,
    ).count()
    previous = evidence.filter(action="provisioning.retry_authorized").count()
    if previous >= MAX_PROVISIONING_RETRIES:
        raise ProvisioningStateError(
            "Provisioning retry limit reached; escalation required."
        )
    if failures != previous + 1:
        raise ProvisioningStateError(
            "Recovery requires a new attributable failed-attempt audit."
        )

    _record_provisioning_audit(
        "provisioning.retry_authorized",
        job_id=locked.id,
        school_id=locked.school_id,
        actor_user_id=actor_user_id,
        correlation_id=correlation_id,
        retry_number=previous + 1,
        reason_code=reason_code,
    )
    locked.state = ProvisioningJob.STATE_QUEUED
    locked.progress = 0
    locked.error = ""
    locked.started_at = None
    locked.finished_at = None
    locked.save(
        update_fields=[
            "state", "progress", "error", "started_at",
            "finished_at", "updated_at",
        ]
    )
    return locked
