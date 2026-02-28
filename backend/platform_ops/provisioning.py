"""
Platform provisioning engine.

Provides two public functions:

  create_school_and_queue_provisioning(...)
      Creates core.School + TenantProfile + SchoolSettings + ProvisioningJob
      atomically inside a transaction.  Idempotent: calling twice with the
      same idempotency_key returns the existing ProvisioningJob unchanged.

  run_provisioning_job(job, ...)
      Executes the provisioning steps in-process.  In production this should
      be called from an async worker (Celery, RQ, etc.); for MVP it runs
      synchronously when the caller invokes it.

Audit trail: every action is recorded via platform_ops.AuditEvent.
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from django.db import transaction

logger = logging.getLogger(__name__)


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
        payload={"name": name, "slug": slug, "plan_code": plan_code},
        request=request,
    )

    logger.info(
        "create_school_and_queue_provisioning: school=%s job=%s",
        school.id,
        job.id,
    )
    return job


def run_provisioning_job(
    job: "ProvisioningJob",
    *,
    actor_user_id: Optional[uuid.UUID] = None,
    request=None,
) -> "ProvisioningJob":
    """
    Execute provisioning steps for a queued job.

    Idempotent: already-succeeded jobs are returned unchanged.
    Steps:
      10% — mark running
      30% — validate TenantProfile exists
      60% — create default SchoolSettings knobs
      90% — set TenantProfile.status = active
     100% — mark succeeded

    On failure: state=failed, error=str(exc), progress unchanged.
    """
    from platform_ops.models import ProvisioningJob  # noqa: PLC0415
    from tenants.models import TenantProfile  # noqa: PLC0415

    if job.state == ProvisioningJob.STATE_SUCCEEDED:
        return job

    try:
        with transaction.atomic():
            # ── Step 1: mark running ─────────────────────────────────────────
            job.state = ProvisioningJob.STATE_RUNNING
            job.started_at = datetime.now(tz=timezone.utc)
            job.progress = 10
            job.save(update_fields=["state", "started_at", "progress", "updated_at"])

            audit(
                "provisioning.started",
                school_id=job.school_id,
                actor_user_id=actor_user_id,
                resource_kind="ProvisioningJob",
                resource_id=job.id,
                payload={"job_id": str(job.id)},
                request=request,
            )

            # ── Step 2: validate TenantProfile ───────────────────────────────
            profile = TenantProfile.objects.select_for_update().get(school=job.school)
            job.progress = 30
            job.save(update_fields=["progress", "updated_at"])

            # ── Step 3: initialise default SchoolSettings knobs ──────────────
            from tenants.models import SchoolSettings  # noqa: PLC0415

            settings_obj, _ = SchoolSettings.objects.get_or_create(school=job.school)
            if not settings_obj.modules:
                settings_obj.modules = {
                    "financial_aid": True,
                    "admissions": True,
                    "gradebook": True,
                    "attendance": True,
                    "billing": True,
                }
                settings_obj.save(update_fields=["modules", "updated_at"])

            job.progress = 60
            job.save(update_fields=["progress", "updated_at"])

            # ── Step 4: activate TenantProfile ───────────────────────────────
            profile.status = "active"
            profile.save(update_fields=["status", "updated_at"])

            job.progress = 90
            job.save(update_fields=["progress", "updated_at"])

            # ── Step 5: mark succeeded ───────────────────────────────────────
            job.state = ProvisioningJob.STATE_SUCCEEDED
            job.progress = 100
            job.finished_at = datetime.now(tz=timezone.utc)
            job.save(update_fields=["state", "progress", "finished_at", "updated_at"])

            audit(
                "provisioning.succeeded",
                school_id=job.school_id,
                actor_user_id=actor_user_id,
                resource_kind="ProvisioningJob",
                resource_id=job.id,
                payload={"job_id": str(job.id)},
                request=request,
            )

    except Exception as exc:
        logger.exception("run_provisioning_job: FAILED job=%s", job.id)
        job.state = ProvisioningJob.STATE_FAILED
        job.error = str(exc)
        job.finished_at = datetime.now(tz=timezone.utc)
        job.save(update_fields=["state", "error", "finished_at", "updated_at"])

        audit(
            "provisioning.failed",
            school_id=job.school_id,
            actor_user_id=actor_user_id,
            resource_kind="ProvisioningJob",
            resource_id=job.id,
            payload={"job_id": str(job.id), "error": str(exc)},
            request=request,
        )

    return job
