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
