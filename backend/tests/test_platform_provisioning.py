"""
Platform provisioning integration tests.

Tests cover:
  1. Idempotency proof: two calls with the same Idempotency-Key → only one
     ProvisioningJob and one TenantProfile created.

  2. Full provisioning lifecycle: run_provisioning_job() takes a queued job
     to state=succeeded with progress=100.
"""
import uuid

import pytest
from django.test import TestCase


@pytest.mark.django_db(transaction=True)
def test_create_school_idempotent(django_user_model):
    """
    Two calls to create_school_and_queue_provisioning() with the same
    idempotency_key must produce exactly one ProvisioningJob record and
    one TenantProfile record.
    """
    from platform_ops.models import ProvisioningJob
    from platform_ops.provisioning import create_school_and_queue_provisioning
    from tenants.models import TenantProfile

    key = str(uuid.uuid4())

    job1 = create_school_and_queue_provisioning(
        name="Idempotency Test School",
        slug=f"idem-test-{key[:8]}",
        idempotency_key=key,
    )

    job2 = create_school_and_queue_provisioning(
        name="Idempotency Test School",
        slug=f"idem-test-{key[:8]}",
        idempotency_key=key,
    )

    # Both calls must return the same job
    assert job1.id == job2.id, "Idempotency failure: two distinct jobs created for the same key"

    # Only one ProvisioningJob should exist for this key
    job_count = ProvisioningJob.objects.filter(idempotency_key=key).count()
    assert job_count == 1, f"Expected 1 ProvisioningJob, found {job_count}"

    # Only one TenantProfile for the school
    profile_count = TenantProfile.objects.filter(school_id=job1.school_id).count()
    assert profile_count == 1, f"Expected 1 TenantProfile, found {profile_count}"


@pytest.mark.django_db(transaction=True)
def test_provisioning_job_runs_to_succeeded(django_user_model):
    """
    run_provisioning_job() must bring a queued job all the way to
    state='succeeded' with progress=100 and activate the TenantProfile.
    """
    from platform_ops.models import ProvisioningJob
    from platform_ops.provisioning import (
        create_school_and_queue_provisioning,
        run_provisioning_job,
    )
    from tenants.models import TenantProfile

    key = str(uuid.uuid4())

    job = create_school_and_queue_provisioning(
        name="Lifecycle Test School",
        slug=f"lifecycle-{key[:8]}",
        idempotency_key=key,
    )

    # Job starts queued
    assert job.state == ProvisioningJob.STATE_QUEUED

    # Run provisioning synchronously
    completed_job = run_provisioning_job(job)

    # Must have reached succeeded
    assert completed_job.state == ProvisioningJob.STATE_SUCCEEDED, (
        f"Expected succeeded, got {completed_job.state}. Error: {completed_job.error}"
    )
    assert completed_job.progress == 100

    # TenantProfile must be activated
    profile = TenantProfile.objects.get(school_id=job.school_id)
    assert profile.status == "active", f"Expected TenantProfile.status='active', got '{profile.status}'"

    # finished_at must be set
    assert completed_job.finished_at is not None, "finished_at should be set on completion"


@pytest.mark.django_db
def test_provisioning_repeat_uses_database_state_not_stale_object():
    """A stale queued instance cannot perform the completed job twice."""
    from platform_ops.models import AuditEvent
    from platform_ops.provisioning import (
        create_school_and_queue_provisioning, run_provisioning_job,
    )

    key = str(uuid.uuid4())
    job = create_school_and_queue_provisioning(
        name="Stale Job School", slug=f"stale-{key[:8]}",
        idempotency_key=key,
    )
    completed = run_provisioning_job(job)
    assert completed.state == "succeeded"
    second = run_provisioning_job(job)
    assert second.state == "succeeded"
    assert AuditEvent.objects.filter(
        resource_id=job.pk, action="provisioning.succeeded"
    ).count() == 1


@pytest.mark.django_db
def test_failed_or_running_job_cannot_restart_implicitly():
    """Operator recovery must be a distinct approved action."""
    from platform_ops.provisioning import (
        ProvisioningStateError, create_school_and_queue_provisioning,
        run_provisioning_job,
    )
    for state in ("running", "failed"):
        key = str(uuid.uuid4())
        job = create_school_and_queue_provisioning(
            name=f"Retry State {state}", slug=f"retry-{key[:8]}",
            idempotency_key=key,
        )
        job.state = state
        job.save(update_fields=["state"])
        with pytest.raises(ProvisioningStateError):
            run_provisioning_job(job)


@pytest.mark.django_db
def test_provisioning_audit_failure_rolls_back_activation(monkeypatch):
    """The school cannot activate when mandatory audit persistence fails."""
    from platform_ops.models import AuditEvent
    from platform_ops.provisioning import (
        ProvisioningAuditError, create_school_and_queue_provisioning,
        run_provisioning_job,
    )
    from tenants.models import TenantProfile

    key = str(uuid.uuid4())
    job = create_school_and_queue_provisioning(
        name="Audit Failure School", slug=f"audit-fail-{key[:8]}",
        idempotency_key=key,
    )
    def fail(*args, **kwargs):
        raise RuntimeError("Sensitive audit database diagnostic")
    monkeypatch.setattr(AuditEvent.objects, "create", fail)
    with pytest.raises(ProvisioningAuditError):
        run_provisioning_job(job)
    job.refresh_from_db()
    assert job.state == "queued"
    assert TenantProfile.objects.get(school_id=job.school_id).status == "pending"


@pytest.mark.django_db
def test_operator_command_defaults_to_read_only_and_rejects_sqlite():
    """Command needs an active owner, exact confirmation and real row locking."""
    from django.contrib.auth import get_user_model
    from django.core.management import call_command
    from django.core.management.base import CommandError
    from platform_ops.provisioning import create_school_and_queue_provisioning

    key = str(uuid.uuid4())
    job = create_school_and_queue_provisioning(
        name="Command Safety School", slug=f"cmd-{key[:8]}",
        idempotency_key=key,
    )
    User = get_user_model()
    staff = User.objects.create_user(username=f"staff-{key[:8]}")
    owner = User.objects.create_superuser(
        username=f"owner-{key[:8]}",
        email=f"{key[:8]}@example.invalid",
        password="test-secret-only",
    )
    with pytest.raises(CommandError, match="superuser"):
        call_command(
            "run_school_provisioning",
            job_id=str(job.pk), actor_id=str(staff.pk),
        )
    call_command("run_school_provisioning", job_id=str(job.pk), actor_id=str(owner.pk))
    with pytest.raises(CommandError, match="Confirm"):
        call_command(
            "run_school_provisioning",
            job_id=str(job.pk), actor_id=str(owner.pk), apply=True,
        )
    # Exercise the refusal deterministically on PostgreSQL and SQLite CI.
    from unittest.mock import patch
    with patch(
        "platform_ops.management.commands.run_school_provisioning.connection"
    ) as mocked_connection:
        mocked_connection.vendor = "sqlite"
        with pytest.raises(CommandError, match="PostgreSQL"):
            call_command(
                "run_school_provisioning",
                job_id=str(job.pk), actor_id=str(owner.pk), apply=True,
                confirm_job_id=str(job.pk),
            )
    job.refresh_from_db()
    assert job.state == "queued"
