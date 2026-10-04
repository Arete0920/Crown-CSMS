import uuid
from datetime import timedelta
import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone
from rest_framework.test import APIClient
from core.models import CrownPermission, RolePermission, School, Staff, UserAccount, UserRole
from hr.models import Employee
from hr.requirement_models import StaffRequirement, StaffRequirementEvent

pytestmark = pytest.mark.django_db
URL = '/api/v1/hr/staff-requirements/'


@pytest.fixture
def context():
    school = School.objects.create(name='Staff requirements school', timezone='UTC')
    user = UserAccount.objects.create_user(username='requirements-reviewer', school=school)
    role = f'requirements-{uuid.uuid4().hex[:8]}'
    UserRole.objects.create(user=user, school=school, role_code=role)
    for code in ('hr.view', 'hr.edit'):
        permission, _ = CrownPermission.objects.get_or_create(code=code)
        RolePermission.objects.create(role_code=role, permission=permission)
    staff = Staff.objects.create(school=school, first_name='Grace', last_name='Teacher',
        email='grace@example.com', role_type='TEACHER')
    client = APIClient(); client.force_authenticate(user)
    return school, user, role, staff, client


def post(c, **data):
    return c[4].post(URL, {'request_key': str(uuid.uuid4()), 'reason': 'School reviewer evidence', **data},
        format='json', HTTP_X_SCHOOL_ID=str(c[0].id))


def create(c, **extra):
    return post(c, operation='create', staff_id=str(c[3].id), title='Annual school training',
        category='training', due_date=timezone.localdate().isoformat(), **extra)


def get(c, **query):
    return c[4].get(URL, query, HTTP_X_SCHOOL_ID=str(c[0].id))


def complete(c, row, **extra):
    return post(c, operation='complete', requirement_id=row['id'], version=row['version'],
        completed_on=timezone.localdate().isoformat(), evidence_reference='school-record:training-001', **extra)


def test_creation_targets_core_staff_and_preserves_safe_retry(context):
    c = context; key = str(uuid.uuid4())
    response = create(c, request_key=key); assert response.status_code == 201
    assert create(c, request_key=key).status_code == 200
    row = StaffRequirement.objects.get()
    assert row.staff == c[3] and row.school == c[0]
    assert StaffRequirementEvent.objects.count() == 1 and not Employee.objects.exists()
    assert post(c, operation='reopen', requirement_id=str(row.id), version=1, request_key=key).status_code == 409


def test_completion_reopen_and_reschedule_retain_prior_evidence(context):
    c = context; row = create(c).data
    response = complete(c, row, valid_until=(timezone.localdate()+timedelta(days=20)).isoformat())
    assert response.status_code == 200
    assert get(c).data['requirements'][0]['status'] == 'expiring'
    reopened = post(c, operation='reopen', requirement_id=row['id'], version=2)
    assert reopened.status_code == 200 and reopened.data['evidence_reference'] == ''
    changed = post(c, operation='reschedule', requirement_id=row['id'], version=3,
        due_date=(timezone.localdate()+timedelta(days=10)).isoformat())
    assert changed.status_code == 200 and changed.data['version'] == 4
    history = get(c, requirement_id=row['id']).data['history']
    assert history['total'] == 4
    assert history['events'][1]['before']['evidence_reference'] == 'school-record:training-001'
    assert get(c).data['summary'] == {'pending': 1}


def test_stale_and_boolean_versions_do_not_change_evidence(context):
    c = context; row = create(c).data
    assert complete(c, row).status_code == 200
    assert complete(c, row).status_code == 409
    assert post(c, operation='reopen', requirement_id=row['id'], version=True).status_code == 409
    assert StaffRequirementEvent.objects.count() == 2


@pytest.mark.parametrize('change', [
    {'completed_on': '2099-01-01'}, {'completed_on': 'invalid'}, {'evidence_reference': ''},
    {'valid_until': '1900-01-01'}, {'valid_until': 'invalid'}, {'reason': ''},
])
def test_invalid_completion_rolls_back_atomically(context, change):
    c = context; row = create(c).data
    values = {'operation': 'complete', 'requirement_id': row['id'], 'version': 1,
        'completed_on': timezone.localdate().isoformat(), 'evidence_reference': 'record', **change}
    assert post(c, **values).status_code == 400
    assert StaffRequirement.objects.get().completed_on is None and StaffRequirementEvent.objects.count() == 1


def test_permissions_are_persistent_school_scoped_and_write_specific(context):
    c = context
    assert c[4].get(URL).status_code == 400
    RolePermission.objects.filter(role_code=c[2], permission__code='hr.edit').delete()
    assert get(c).status_code == 200 and get(c).data['can_edit'] is False
    assert create(c).status_code == 403
    RolePermission.objects.filter(role_code=c[2]).delete()
    assert get(c).status_code == 403
    assert c[4].get(URL).status_code in {400, 403}


def test_foreign_school_and_inactive_accounts_are_rejected(context):
    c = context; foreign = School.objects.create(name='Foreign requirements tenant')
    staff = Staff.objects.create(school=foreign, first_name='Other', last_name='Staff', email='other@example.com', role_type='TEACHER')
    assert post(c, operation='create', staff_id=str(staff.id), title='Foreign', category='training', due_date='2026-10-03').status_code == 404
    row = StaffRequirement.objects.create(school=foreign, staff=staff, title='Foreign', category='training', due_date='2026-10-03')
    assert get(c, requirement_id=str(row.id)).status_code == 404
    assert post(c, operation='reopen', requirement_id=str(row.id), version=1).status_code == 404
    # Canonical tenant middleware conceals a school outside the actor's scope.
    assert c[4].get(URL, HTTP_X_SCHOOL_ID=str(foreign.id)).status_code == 404
    c[1].is_active = False; c[1].save()
    assert get(c).status_code == 403


def test_canonical_staff_must_be_active_for_new_requirements(context):
    c = context; c[3].status = 'INACTIVE'; c[3].save()
    assert create(c).status_code == 404 and get(c).data['staff'] == []


def test_summary_and_pagination_are_full_window_and_expiry_is_inclusive(context):
    c = context; today = timezone.localdate()
    for index in range(105):
        StaffRequirement.objects.create(school=c[0], staff=c[3], title=f'Requirement {index}', category='training', due_date=today-timedelta(days=1))
    for title, expiry in [('Expired', today-timedelta(days=1)), ('Expiring', today), ('Complete', today+timedelta(days=31))]:
        StaffRequirement.objects.create(school=c[0], staff=c[3], title=title, category='certification', due_date=today,
            completed_on=today-timedelta(days=2), valid_until=expiry, evidence_reference='school-record')
    first = get(c).data
    assert len(first['requirements']) == 100 and first['total'] == 108 and first['next_offset'] == 100
    assert first['summary'] == {'overdue': 105, 'expired': 1, 'expiring': 1, 'complete': 1}
    assert len(get(c, offset=100).data['requirements']) == 8
    assert get(c, offset=-1).status_code == 400 and get(c, offset='invalid').status_code == 400


def test_model_tenant_validation_and_append_only_history(context):
    c = context; create(c)
    foreign = School.objects.create(name='Wrong requirement authority')
    with pytest.raises(ValidationError):
        StaffRequirement.objects.create(school=foreign, staff=c[3], title='Wrong', category='training', due_date=timezone.localdate())
    event = StaffRequirementEvent.objects.get()
    with pytest.raises(ValidationError): event.save()
    with pytest.raises(ValidationError): event.delete()
    with pytest.raises(ValidationError): StaffRequirementEvent.objects.all().update(reason='Rewrite')
    with pytest.raises(ValidationError): StaffRequirementEvent.objects.all().delete()
    with pytest.raises(ValidationError): StaffRequirement.objects.all().delete()
    with pytest.raises(ValidationError): StaffRequirement.objects.all().update(title='Rewrite')
    with pytest.raises(ValidationError): StaffRequirement.objects.bulk_update([], ['title'])
    with pytest.raises(ValidationError): StaffRequirement.objects.bulk_create([])


@pytest.mark.parametrize('field', ['school_id', 'staff_id', 'title', 'category'])
def test_requirement_ownership_and_definition_cannot_be_reassigned(context, field):
    c = context; create(c)
    row = StaffRequirement.objects.get()
    original = getattr(row, field)
    setattr(row, field, uuid.uuid4() if field.endswith('_id') else 'Reassigned')
    with pytest.raises(ValidationError): row.save()
    row.refresh_from_db()
    assert getattr(row, field) == original and StaffRequirementEvent.objects.count() == 1


def test_staff_search_and_selected_staff_never_expand_scope(context):
    c = context; create(c)
    assert get(c, staff_search='Grace').data['staff_total'] == 1
    assert get(c, staff_search='Unrelated').data['staff_total'] == 0
    assert get(c, staff_id=str(c[3].id)).data['total'] == 1
    assert get(c, staff_id=str(uuid.uuid4())).status_code == 404


@pytest.mark.parametrize('payload', [{'operation': []}, {'operation': 'create', 'staff_id': str(uuid.uuid4()), 'category': []}, {'operation': 'delete'}, {'operation': 'create', 'staff_id': 'invalid'},
    {'operation': 'create', 'staff_id': None}, {'operation': 'reopen', 'requirement_id': 'invalid', 'version': 1}])
def test_invalid_operations_and_identifiers_fail_closed(context, payload):
    if 'category' in payload:
        payload = {**payload, 'staff_id': str(context[3].id)}
    assert post(context, **payload).status_code == 400


def test_review_history_pages_retain_every_event(context):
    c = context; row = create(c).data
    for version in range(1, 103):
        assert post(c, operation='reschedule', requirement_id=row['id'], version=version,
            due_date=timezone.localdate().isoformat()).status_code == 200
    first = get(c, requirement_id=row['id']).data['history']
    second = get(c, requirement_id=row['id'], history_offset=100).data['history']
    assert first['total'] == 103 and first['next_offset'] == 100
    assert len(first['events']) == 100 and len(second['events']) == 3
    assert second['events'][-1]['version'] == 1 and second['next_offset'] is None
    assert get(c, requirement_id=row['id'], history_offset=-1).status_code == 400
    assert get(c, requirement_id=row['id'], history_offset='bad').status_code == 400


def test_requirement_dates_use_school_calendar_at_utc_midnight(context, monkeypatch):
    from datetime import datetime, timezone as dt_timezone
    c=context; c[0].timezone='America/New_York'; c[0].save()
    monkeypatch.setattr(timezone, 'now', lambda: datetime(2026,10,4,2,tzinfo=dt_timezone.utc))
    row=create(c).data
    assert post(c,operation='complete',requirement_id=row['id'],version=1,completed_on='2026-10-04',evidence_reference='record').status_code == 400
    assert post(c,operation='complete',requirement_id=row['id'],version=1,completed_on='2026-10-03',valid_until='2026-10-03',evidence_reference='record').status_code == 200
    data=get(c).data
    assert data['today'] == '2026-10-03' and data['requirements'][0]['status'] == 'expiring'


def test_invalid_school_timezone_fails_closed(context):
    c=context; c[0].timezone='Invalid/School'; c[0].save()
    assert get(c).status_code == 400 and create(c).status_code == 400
