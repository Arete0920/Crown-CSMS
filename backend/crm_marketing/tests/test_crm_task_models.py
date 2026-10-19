"""Staged CRM task integrity tests; no routes or senders enabled."""
import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone

from core.models import School
from crm_marketing.models import CRMTask, CRMTaskEvent, MarketingLead, ProspectGroup

pytestmark = pytest.mark.django_db


def test_task_requires_local_relationship():
    school = School.objects.create(name="CRM Tasks School")
    foreign = School.objects.create(name="Other CRM Tasks School")
    lead = MarketingLead.objects.create(school=foreign)
    with pytest.raises(ValidationError):
        CRMTask.objects.create(school=school, lead=lead, title="Call family", created_by_user_id=school.pk)
    assert CRMTask.objects.count() == 0


def test_task_completion_has_coherent_actor_and_time():
    school = School.objects.create(name="CRM Task Completion School")
    group = ProspectGroup.objects.create(school=school, label="Prospect Family")
    task = CRMTask.objects.create(school=school, group=group, title="Call family", created_by_user_id=school.pk)
    task.state = CRMTask.State.DONE
    with pytest.raises(ValidationError):
        task.save()
    task.completed_at = timezone.now()
    task.completed_by_user_id = school.pk
    task.save()
    task.refresh_from_db()
    assert task.state == CRMTask.State.DONE
    assert task.completed_at and task.completed_by_user_id


def test_task_idempotency_db_constraint_is_scoped_to_school():
    a = School.objects.create(name="CRM Task Unique A")
    b = School.objects.create(name="CRM Task Unique B")
    group_a = ProspectGroup.objects.create(school=a, label="Prospect A")
    group_b = ProspectGroup.objects.create(school=b, label="Prospect B")
    common = "call-request-42"
    CRMTask.objects.create(
        school=a, group=group_a, title="Call", created_by_user_id=a.pk, idempotency_key=common,
    )
    CRMTask.objects.create(
        school=b, group=group_b, title="Call", created_by_user_id=b.pk, idempotency_key=common,
    )
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            CRMTask.objects.bulk_create([
                CRMTask(school=a, group=group_a, title="Duplicate", created_by_user_id=a.pk, idempotency_key=common),
            ])
    assert CRMTask.objects.count() == 2


def test_audit_events_are_school_scoped_and_immutable():
    a = School.objects.create(name="CRM Audit A")
    b = School.objects.create(name="CRM Audit B")
    group = ProspectGroup.objects.create(school=a, label="Family")
    task = CRMTask.objects.create(school=a, group=group, title="Follow up", created_by_user_id=a.pk)
    with pytest.raises(ValidationError):
        CRMTaskEvent.objects.create(
            school=b, task=task, kind=CRMTaskEvent.Kind.CREATED, actor_user_id=b.pk,
        )
    event = CRMTaskEvent.objects.create(
        school=a, task=task, kind=CRMTaskEvent.Kind.CREATED, actor_user_id=a.pk,
    )
    with pytest.raises(ValidationError):
        event.save()
    assert CRMTaskEvent.objects.count() == 1
