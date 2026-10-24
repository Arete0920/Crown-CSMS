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
def test_operator_command_defaults_to_read_only_and_rejects_sqlite(monkeypatch):
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
    # Neither a plausible actor UUID nor --apply authorizes an unspecified,
    # production, or conflicting hosted execution environment.
    for label in ("", "prod", "production"):
        monkeypatch.setenv("CROWN_ENV", label)
        with pytest.raises(CommandError, match="DEV environment"):
            call_command(
                "run_school_provisioning",
                job_id=str(job.pk), actor_id=str(owner.pk),
                apply=True, confirm_job_id=str(job.pk),
            )
    monkeypatch.setenv("CROWN_ENV", "dev")
    monkeypatch.setenv("DJANGO_ENV", "production")
    with pytest.raises(CommandError, match="DEV environment"):
        call_command(
            "run_school_provisioning",
            job_id=str(job.pk), actor_id=str(owner.pk),
            apply=True, confirm_job_id=str(job.pk),
        )
    monkeypatch.delenv("DJANGO_ENV", raising=False)
    monkeypatch.setenv("WEBSITE_HOSTNAME", "crown-api-prod.azurewebsites.net")
    with pytest.raises(CommandError, match="DEV environment"):
        call_command(
            "run_school_provisioning",
            job_id=str(job.pk), actor_id=str(owner.pk),
            apply=True, confirm_job_id=str(job.pk),
        )
    monkeypatch.delenv("WEBSITE_HOSTNAME", raising=False)
    monkeypatch.setenv("CROWN_ENV", "dev")
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
    # A DEV environment label or active owner UUID must not authorize writes
    # against an unrelated/production PostgreSQL server.
    monkeypatch.setenv("WEBSITE_HOSTNAME", "crown-api-dev.azurewebsites.net")
    for host, sslmode in (
        ("crown-pg-prod.postgres.database.azure.com", "verify-full"),
        ("crown-pg-dev.postgres.database.azure.com", "require"),
    ):
        with patch(
            "platform_ops.management.commands.run_school_provisioning.connection"
        ) as db, patch(
            "platform_ops.management.commands.run_school_provisioning.run_provisioning_job"
        ) as activate:
            db.vendor = "postgresql"
            db.settings_dict = {
                "HOST": host, "PORT": "5432", "NAME": "crown",
                "OPTIONS": {"sslmode": sslmode},
            }
            with pytest.raises(CommandError, match="pinned DEV PostgreSQL"):
                call_command(
                    "run_school_provisioning",
                    job_id=str(job.pk), actor_id=str(owner.pk), apply=True,
                    confirm_job_id=str(job.pk),
                )
            db.cursor.assert_not_called()
            activate.assert_not_called()
    job.refresh_from_db()
    assert job.state == "queued"


def test_provisioning_dev_target_identity_and_tls_guards(monkeypatch):
    """Pin Azure target and verify actual PostgreSQL identity before mutation."""
    from unittest.mock import MagicMock
    from django.core.management.base import CommandError
    from platform_ops.management.commands.run_school_provisioning import (
        _verify_dev_postgresql_target,
    )

    monkeypatch.setenv("CROWN_ENV", "dev")
    monkeypatch.setenv("WEBSITE_HOSTNAME", "crown-api-dev.azurewebsites.net")
    db = MagicMock()
    db.vendor = "postgresql"
    db.settings_dict = {
        "HOST": "crown-pg-dev.postgres.database.azure.com",
        "PORT": "5432", "NAME": "crown",
        "OPTIONS": {"sslmode": "verify-full"},
    }
    cursor = db.cursor.return_value.__enter__.return_value
    cursor.fetchone.side_effect = [("crown", "public", False), (True,)]
    _verify_dev_postgresql_target(db)
    assert cursor.execute.call_count == 2

    for rows, message in (
        ([("different_database", "public", False)], "identity does not match"),
        ([("crown", "public", True)], "identity does not match"),
        ([("crown", "public", False), (False,)], "TLS is not verified"),
    ):
        cursor.fetchone.side_effect = rows
        with pytest.raises(CommandError, match=message):
            _verify_dev_postgresql_target(db)


@pytest.mark.django_db(transaction=True)
def test_postgresql_parallel_provisioning_claims_once():
    """Two independent PostgreSQL connections activate a school exactly once."""
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event
    from time import sleep

    from django.db import close_old_connections, connection
    from platform_ops.models import AuditEvent, ProvisioningJob
    from platform_ops import provisioning
    from tenants.models import TenantProfile

    if connection.vendor != "postgresql":
        pytest.skip("PostgreSQL row locks are required for this proof")

    key = str(uuid.uuid4())
    job = provisioning.create_school_and_queue_provisioning(
        name="Parallel Provisioning School",
        slug=f"parallel-{key[:8]}",
        idempotency_key=key,
    )

    first_has_lock = Event()
    release_first = Event()
    original_audit = provisioning._record_provisioning_audit

    def paused_audit(action, **kwargs):
        if action == "provisioning.started":
            first_has_lock.set()
            if not release_first.wait(timeout=20):
                raise RuntimeError("Parallel test timed out waiting for release")
        return original_audit(action, **kwargs)

    def execute():
        close_old_connections()
        try:
            # Each worker receives a stale object, so only the persisted
            # row lock can serialize these attempts correctly.
            return provisioning.run_provisioning_job(job).state
        finally:
            close_old_connections()

    # The first worker has locked the job when "started" audit is reached.
    # Release it only after the second database session is submitted.
    with pytest.MonkeyPatch.context() as patcher:
        patcher.setattr(provisioning, "_record_provisioning_audit", paused_audit)
        with ThreadPoolExecutor(max_workers=2) as pool:
            first = pool.submit(execute)
            try:
                assert first_has_lock.wait(timeout=20), "First worker never claimed job"
                second = pool.submit(execute)
                sleep(0.15)
            finally:
                release_first.set()
            assert first.result(timeout=35) == ProvisioningJob.STATE_SUCCEEDED
            assert second.result(timeout=35) == ProvisioningJob.STATE_SUCCEEDED

    job.refresh_from_db()
    assert job.progress == 100
    assert job.state == ProvisioningJob.STATE_SUCCEEDED
    assert TenantProfile.objects.get(school_id=job.school_id).status == "active"
    assert AuditEvent.objects.filter(
        resource_id=job.id, action="provisioning.started"
    ).count() == 1
    assert AuditEvent.objects.filter(
        resource_id=job.id, action="provisioning.succeeded"
    ).count() == 1


@pytest.mark.django_db(transaction=True)
def test_postgresql_operator_command_executes_one_job():
    """The confirmed PostgreSQL command creates one durable activation."""
    from io import StringIO

    from django.contrib.auth import get_user_model
    from django.core.management import call_command
    from django.db import connection
    from platform_ops.models import AuditEvent, ProvisioningJob
    from platform_ops.provisioning import create_school_and_queue_provisioning
    from tenants.models import TenantProfile

    if connection.vendor != "postgresql":
        pytest.skip("PostgreSQL command execution requires real PostgreSQL")

    key = str(uuid.uuid4())
    job = create_school_and_queue_provisioning(
        name="Command PostgreSQL School",
        slug=f"cmd-pg-{key[:8]}",
        idempotency_key=key,
    )
    operator = get_user_model().objects.create_superuser(
        username=f"operator-{key[:8]}",
        email=f"{key[:8]}@example.invalid",
        password="local-test-only",
    )
    output = StringIO()
    call_command(
        "run_school_provisioning",
        job_id=str(job.id),
        actor_id=str(operator.id),
        apply=True,
        confirm_job_id=str(job.id),
        stdout=output,
    )
    job.refresh_from_db()
    assert job.state == ProvisioningJob.STATE_SUCCEEDED
    assert TenantProfile.objects.get(school_id=job.school_id).status == "active"
    assert AuditEvent.objects.filter(
        resource_id=job.id, action="provisioning.succeeded",
        actor_user_id=operator.id,
    ).count() == 1
    assert "PROVISIONED" in output.getvalue()


@pytest.mark.django_db
def test_school_creation_rolls_back_when_audit_write_fails(monkeypatch):
    """A failed required audit write must roll back the school and queued job."""
    from core.models import School
    from platform_ops.models import AuditEvent, ProvisioningJob
    from platform_ops.provisioning import (
        ProvisioningAuditError,
        create_school_and_queue_provisioning,
    )
    from tenants.models import TenantProfile

    key = str(uuid.uuid4())
    slug = f"unaudited-{key[:8]}"

    def broken_audit(*args, **kwargs):
        raise RuntimeError("sensitive database diagnostic")

    monkeypatch.setattr(AuditEvent.objects, "create", broken_audit)
    with pytest.raises(ProvisioningAuditError):
        create_school_and_queue_provisioning(
            name="Unaudited Synthetic School",
            slug=slug,
            idempotency_key=key,
        )
    assert not School.objects.filter(name="Unaudited Synthetic School").exists()
    assert not TenantProfile.objects.filter(slug=slug).exists()
    assert not ProvisioningJob.objects.filter(idempotency_key=key).exists()
