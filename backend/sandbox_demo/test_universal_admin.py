"""Actual admin writes, independent reload, isolation and lifecycle retention."""
from uuid import uuid4
import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from core.models import Family, School, UserRole
from crown_api.models import AttendanceRecord
from crown_api.models_comms_core import Message, MessageThread
from sandbox_demo.test_universal_access import operator_secrets, login
from sandbox_demo.test_universal_presenter import local_runtime
from sandbox_demo.universal_admin import prepare_presenter_admin
from sandbox_demo.universal_demo import prepare_presenter
from sandbox_demo.universal_identity import UNIVERSAL_SCHOOL_ID
from rest_framework.test import APIClient

pytestmark = pytest.mark.django_db
BASE = '/api/v1/presenter/admin/'


@pytest.fixture
def ready(local_runtime, operator_secrets):
    from io import StringIO
    call_command('seed_permissions', stdout=StringIO())
    prepare_presenter(apply=True, enable_password_login=True)
    assert prepare_presenter_admin()['mode'] == 'PREFLIGHT'
    assert not AttendanceRecord.objects.exists()
    prepare_presenter_admin(apply=True)


def test_normal_admin_resolves_household_attendance_and_internal_followup(ready, operator_secrets):
    admin, _ = login('school_admin', operator_secrets)
    before = admin.get(BASE + 'state/')
    assert before.status_code == 200, before.content
    original = before.json()
    assert original['exception_status'] == 'open' and original['communication_status'] == 'pending'
    assert original['enrollment_status'] == 'ENROLLED' and original['tuition_context_cents'] > 0
    assert original['finance_open_obligation_count'] > 0 and original['academic_context']
    assert not Message.objects.exists()
    foreign = School.objects.create(name='Separate fictional administration school')
    untouched = Family.objects.create(school=foreign, family_name=original['family_name'], address_line2='Preserve')
    for _ in range(2):
        result = admin.post(BASE + 'resolve-operational-exception/', {}, format='json')
        assert result.status_code == 200, result.content
        assert result.json()['attendance_exception_resolved'] and result.json()['student_household_update_persisted']
        readback = admin.get(BASE + 'state/').json()
        assert readback['household_note'] == 'Admin-verified demo household'
        assert readback['attendance_status'] == AttendanceRecord.STATUS_EXCUSED
        assert readback['communication_status'] == 'sent' and not readback['is_platform_superuser']
    assert Message.objects.count() == MessageThread.objects.count() == 1
    attendance = AttendanceRecord.objects.get(student_id=original['student_id'])
    assert attendance.section.school_id == UNIVERSAL_SCHOOL_ID
    untouched.refresh_from_db()
    assert untouched.address_line2 == 'Preserve'
    with pytest.raises(CommandError, match='Existing administrative'):
        prepare_presenter_admin(apply=True)


def test_wrong_roles_foreign_selector_runtime_and_revocation_deny(ready, operator_secrets, settings):
    admin, tokens = login('school_admin', operator_secrets)
    assert APIClient().get(BASE + 'state/', HTTP_X_SCHOOL_ID=str(UNIVERSAL_SCHOOL_ID)).status_code == 401
    for key in ('parent', 'teacher', 'board', 'finance_director'):
        actor, _ = login(key, operator_secrets)
        assert actor.get(BASE + 'state/').status_code == 404
        assert actor.post(BASE + 'resolve-operational-exception/', {}, format='json').status_code == 404
    assert admin.post(BASE + 'resolve-operational-exception/', {'student_id': str(uuid4())}, format='json').status_code == 400
    assert admin.get(BASE + 'state/', {'school_id': str(uuid4())}).status_code == 400
    foreign = School.objects.create(name='Other fictional admin scope')
    admin.credentials(HTTP_AUTHORIZATION='Bearer ' + tokens['access'], HTTP_X_SCHOOL_ID=str(foreign.pk))
    assert admin.get(BASE + 'state/').status_code == 404
    admin.credentials(HTTP_AUTHORIZATION='Bearer ' + tokens['access'], HTTP_X_SCHOOL_ID=str(UNIVERSAL_SCHOOL_ID))
    UserRole.objects.filter(user__username__contains='.school_admin@').delete()
    assert admin.get(BASE + 'state/').status_code == 404
    settings.CROWN_ENV = 'production'
    assert admin.post(BASE + 'resolve-operational-exception/', {}, format='json').status_code == 404
    assert not Message.objects.exists()


def test_rollover_preserves_old_admin_history_and_replays_new_scope(ready, operator_secrets):
    from sandbox_demo.universal_care import prepare_presenter_care
    from sandbox_demo.universal_jireh import prepare_presenter_jireh
    from sandbox_demo.universal_admissions import prepare_presenter_admissions
    from sandbox_demo.universal_identity import presenter_username
    from sandbox_demo.universal_reset import rollover_presenter
    prepare_presenter_care(apply=True)
    prepare_presenter_jireh(apply=True)
    prepare_presenter_admissions(apply=True)
    admin, _ = login('school_admin', operator_secrets)
    assert admin.post(BASE + 'resolve-operational-exception/', {}, format='json').status_code == 200
    old_message = Message.objects.get()
    result = rollover_presenter(expected_current=UNIVERSAL_SCHOOL_ID, request_key=uuid4(),
        apply=True, enable_password_login=True)
    assert admin.get(BASE + 'state/').status_code == 404
    fresh = APIClient()
    token = fresh.post('/api/v1/auth/token/', {'username': presenter_username('school_admin', result['school_id']),
        'password': operator_secrets['school_admin']}, format='json')
    assert token.status_code == 200, token.content
    fresh.credentials(HTTP_AUTHORIZATION='Bearer ' + token.json()['access'], HTTP_X_SCHOOL_ID=result['school_id'])
    state = fresh.get(BASE + 'state/')
    assert state.status_code == 200, state.content
    assert state.json()['exception_status'] == 'open' and state.json()['communication_status'] == 'pending'
    assert fresh.post(BASE + 'resolve-operational-exception/', {}, format='json').status_code == 200
    assert Message.objects.count() == 2 and Message.objects.filter(pk=old_message.pk).exists()
    assert old_message.thread.student.school_id == UNIVERSAL_SCHOOL_ID
