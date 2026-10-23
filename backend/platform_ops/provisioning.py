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

    Never raises — audit failures are logged but never surface to callers.
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
        logger.error("audit() failed — action=%s error=%s", action, exc)


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
) -> "ProvisioningJob":
    """
    Idempotently create a school tenant and queue its provisioning job.

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
        return existing

    payment_provider = normalize_payment_provider(payment_provider)

    # ── Create core.School ──────────────────────────────────────────────────
    from core.models import School  # noqa: PLC0415

    school = School.objects.create(name=name)

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

    # ── Audit ────────────────────────────────────────────────────────────────
    audit(
        "school.created",
        school_id=school.id,
        actor_user_id=actor_user_id,
        resource_kind="School",
        resource_id=school.id,
        payload={
            "name": name,
            "slug": slug,
            "plan_code": plan_code,
            "payment_provider": payment_provider,
        },
        request=request,
    )

    logger.info(
        "create_school_and_queue_provisioning: school=%s job=%s",
        school.id,
        job.id,
    )
    return job


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
) -> None:
    """Persist a minimal audit event or fail the entire state transition."""
    from platform_ops.models import AuditEvent

    try:
        AuditEvent.objects.create(
            action=action,
            school_id=school_id,
            actor_user_id=actor_user_id,
            resource_kind="ProvisioningJob",
            resource_id=job_id,
            payload={"job_id": str(job_id)},
        )
    except Exception as exc:
        raise ProvisioningAuditError(
            "Required provisioning audit event could not be persisted."
        ) from exc


def run_provisioning_job(
    job: "ProvisioningJob",
    *,
    actor_user_id: Optional[uuid.UUID] = None,
    request=None,
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

            _record_provisioning_audit(
                "provisioning.succeeded",
                job_id=locked.pk,
                school_id=locked.school_id,
                actor_user_id=actor_user_id,
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
