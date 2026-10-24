"""Fail-closed school onboarding checklist readiness contracts."""
import uuid

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from core.models import School
from onboarding.models_tasks import (
    DEFAULT_TASKS, OnboardingTask, can_activate_school, seed_onboarding_tasks,
)


@pytest.mark.django_db
def test_missing_required_tasks_do_not_make_school_launch_ready():
    school = School.objects.create(name="Synthetic Partial Checklist")
    assert can_activate_school(school) is False
    OnboardingTask.objects.create(
        school=school, task_name=DEFAULT_TASKS[0], status=OnboardingTask.STATUS_COMPLETE
    )
    assert can_activate_school(school) is False
    seed_onboarding_tasks(school)
    assert OnboardingTask.objects.filter(school=school).count() == len(DEFAULT_TASKS)
    assert can_activate_school(school) is False
    OnboardingTask.objects.filter(school=school).update(status=OnboardingTask.STATUS_COMPLETE)
    assert can_activate_school(school) is True
    OnboardingTask.objects.create(school=school, task_name="Additional required review")
    assert can_activate_school(school) is False
    OnboardingTask.objects.filter(school=school, task_name="Additional required review").update(
        status=OnboardingTask.STATUS_COMPLETE
    )
    assert can_activate_school(school) is True


@pytest.mark.django_db
def test_progress_seeds_missing_tasks_and_activation_gate_reports_them():
    school = School.objects.create(name="Synthetic Checklist Endpoint")
    user = get_user_model().objects.create_user(
        username=f"checklist-{uuid.uuid4().hex}", school=school
    )
    OnboardingTask.objects.create(
        school=school, task_name=DEFAULT_TASKS[0], status=OnboardingTask.STATUS_COMPLETE
    )
    client = APIClient()
    client.force_authenticate(user=user)

    def get(route):
        return client.get(f"/api/v1/onboarding/{school.pk}/{route}/",
                          HTTP_X_SCHOOL_ID=str(school.pk))

    gate = get("can-activate")
    assert gate.status_code == 200
    assert gate.data["can_activate"] is False
    assert set(gate.data["pending_tasks"]) == set(DEFAULT_TASKS[1:])
    assert OnboardingTask.objects.filter(school=school).count() == 1

    progress = get("progress")
    assert progress.status_code == 200
    assert progress.data["total_tasks"] == len(DEFAULT_TASKS)
    assert progress.data["completed"] == 1
    assert progress.data["percent_complete"] < 100
    assert OnboardingTask.objects.filter(school=school).count() == len(DEFAULT_TASKS)

    OnboardingTask.objects.filter(school=school).update(status=OnboardingTask.STATUS_COMPLETE)
    gate = get("can-activate")
    assert gate.status_code == 200
    assert gate.data["can_activate"] is True
    assert gate.data["pending_tasks"] == []


@pytest.mark.django_db
def test_unknown_status_never_counts_as_readiness():
    school = School.objects.create(name="Synthetic Invalid Status")
    seed_onboarding_tasks(school)
    OnboardingTask.objects.filter(school=school).update(status=OnboardingTask.STATUS_COMPLETE)
    OnboardingTask.objects.filter(school=school, task_name=DEFAULT_TASKS[0]).update(
        status="invalid"
    )
    assert can_activate_school(school) is False
