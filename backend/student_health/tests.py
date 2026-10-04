import uuid
from datetime import date, timedelta
from decimal import Decimal
import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone
from rest_framework.test import APIClient
from core.models import School, Family, Student, Guardian, UserAccount, UserRole, CrownPermission, RolePermission
from student_health.models import MedicationAuthorization, HealthEntry, HealthMutation

pytestmark = pytest.mark.django_db
URL = '/api/v1/student-health/workspace/'

@pytest.fixture
def context():
    school = School.objects.create(name='Clinical test school', timezone='UTC')
    family = Family.objects.create(school=school, family_name='Clinical family')
    student = Student.objects.create(school=school, family=family, student_number='HEALTH-001', first_name='Casey', last_name='Student', dob=date(2014, 1, 1), status='ACTIVE')
    guardian = Guardian.objects.create(school=school, family=family, first_name='Jamie', last_name='Guardian', email='clinical@example.com', relationship='GUARDIAN')
    user = UserAccount.objects.create_user(username='clinical-reviewer', school=school)
    role = 'clinical-test-'+uuid.uuid4().hex[:8]
    UserRole.objects.create(user=user, school=school, role_code=role)
    for code in ('student_health.view', 'student_health.edit'):
        permission, _ = CrownPermission.objects.get_or_create(code=code)
        RolePermission.objects.create(role_code=role, permission=permission)
    client = APIClient(); client.force_authenticate(user)
    return school, student, guardian, user, role, client


def post(c, **data):
    return c[5].post(URL, {'request_key': str(uuid.uuid4()), 'student_id': str(c[1].id), 'reason': 'Reviewed source record', **data}, format='json', HTTP_X_SCHOOL_ID=str(c[0].id))


def get(c, **params):
    return c[5].get(URL, {'student_id': str(c[1].id), **params}, HTTP_X_SCHOOL_ID=str(c[0].id))


def authorize(c, **extra):
    today = timezone.localdate()
    return post(c, **dict(operation='authorize', guardian_id=str(c[2].id), guardian_authority_verified=True,
        medication='Documented medication', dose='1.000', unit='documented-unit', route='documented-route',
        directions='Directions transcribed from signed order', order_evidence='source:order', consent_evidence='source:consent',
        starts_on=(today-timedelta(days=1)).isoformat(), ends_on=(today+timedelta(days=10)).isoformat()) | extra)


def record(c, **extra):
    return post(c, **dict(operation='record', kind='visit', occurred_at=(timezone.now()-timedelta(minutes=1)).isoformat(),
        topic='Recorded school visit', summary='Staff recorded observation') | extra)


def test_visit_retry_and_correction_preserve_chart_and_reason(context):
    c = context; key = str(uuid.uuid4()); stamp=(timezone.now()-timedelta(minutes=1)).isoformat()
    first=record(c, request_key=key, occurred_at=stamp); assert first.status_code == 201
    assert record(c, request_key=key, occurred_at=stamp).status_code == 200
    assert record(c, request_key=key, occurred_at=stamp, summary='Different').status_code == 409
    corrected=record(c, corrects_id=first.data['entry_id'], summary='Corrected observation', reason='Source clarified')
    assert corrected.status_code == 201
    assert record(c, corrects_id=first.data['entry_id']).status_code == 409
    assert HealthEntry.objects.count() == 2 and HealthMutation.objects.count() == 2
    data=get(c).data
    assert data['summary'] == {'visit': 1}
    assert next(e for e in data['entries'] if str(e['id']) == first.data['entry_id'])['superseded'] is True
    assert data['history'][0]['reason'] == 'Source clarified'


@pytest.mark.parametrize('extra', [{'operation': []}, {'kind': []}, {'occurred_at': 'invalid'}, {'occurred_at': '2026-01-01T12:00:00'},
    {'occurred_at': '2099-01-01T12:00:00Z'}, {'occurred_at': '2010-01-01T12:00:00Z'},
    {'follow_up_on': '1900-01-01'}, {'kind': 'care_plan'}, {'kind': 'immunization'}, {'topic': ''}, {'reason': ''}])
def test_invalid_entries_leave_no_chart_or_mutation(context, extra):
    assert record(context, **extra).status_code == 400
    assert not HealthEntry.objects.exists() and not HealthMutation.objects.exists()


@pytest.mark.parametrize('extra', [{'dose': 'NaN'}, {'dose': '0'}, {'dose': '-1'}, {'dose': '1.0001'},
    {'dose': '100000'}, {'consent_evidence': ''}, {'order_evidence': ''}, {'guardian_authority_verified': False},
    {'ends_on': '1900-01-01'}])
def test_invalid_authorization_is_atomic(context, extra):
    assert authorize(context, **extra).status_code == 400
    assert not MedicationAuthorization.objects.exists() and not HealthMutation.objects.exists()


@pytest.mark.parametrize('flag', [True, None])
def test_unresolved_guardian_authority_cannot_authorize(context, flag):
    c=context; c[2].custody_flag=flag; c[2].save()
    assert authorize(c).status_code == 400 and get(c).data['guardians'] == []


def test_administration_records_exact_source_dose_and_refusal_without_dose(context):
    c=context; order=authorize(c); assert order.status_code == 201
    payload={'kind': 'administration', 'authorization_id': order.data['authorization_id'], 'administration_state': 'given', 'administered_dose': '1', 'administered_unit': 'documented-unit'}
    assert record(c, **payload).status_code == 201
    assert record(c, **{**payload,'administration_state':[]}).status_code == 400
    assert record(c, **{**payload,'administered_dose':'2'}).status_code == 400
    assert record(c, **{**payload,'administered_unit':'converted-unit'}).status_code == 400
    assert record(c, **{**payload,'administration_state':'refused'}).status_code == 400
    assert record(c, kind='administration', authorization_id=order.data['authorization_id'], administration_state='refused').status_code == 201
    assert HealthEntry.objects.count() == 2


def test_revocation_survives_later_custody_change_and_blocks_new_administration(context):
    c=context; order=authorize(c).data
    c[2].custody_flag=True; c[2].save()
    assert record(c, kind='administration', authorization_id=order['authorization_id'], administration_state='not_given').status_code == 400
    for version in (True, 1.0, 2):
        assert post(c, operation='revoke', authorization_id=order['authorization_id'], version=version).status_code == 409
    assert post(c, operation='revoke', authorization_id=order['authorization_id'], version=1).status_code == 200
    c[2].custody_flag=False; c[2].save()
    assert record(c, kind='administration', authorization_id=order['authorization_id'], administration_state='given', administered_dose='1', administered_unit='documented-unit', occurred_at=timezone.now().isoformat()).status_code == 400
    assert post(c, operation='revoke', authorization_id=order['authorization_id'], version=2).status_code == 409


def test_authorization_period_and_patient_are_enforced(context):
    c=context; order=authorize(c).data
    assert record(c, kind='administration', authorization_id=order['authorization_id'], administration_state='not_given', occurred_at=(timezone.now()-timedelta(days=2)).isoformat()).status_code == 400
    other=Student.objects.create(school=c[0], family=c[1].family, student_number='HEALTH-002', first_name='Other', last_name='Student', dob=date(2014,1,1), status='ACTIVE')
    assert record(c, student_id=str(other.id), kind='administration', authorization_id=order['authorization_id'], administration_state='not_given').status_code == 404


def test_generic_health_permission_does_not_grant_clinical_access(context):
    c=context
    RolePermission.objects.filter(role_code=c[4]).delete()
    permission,_=CrownPermission.objects.get_or_create(code='health.view')
    RolePermission.objects.create(role_code=c[4], permission=permission)
    assert get(c).status_code == 403 and record(c).status_code == 403


def test_read_write_permissions_tenant_and_inactive_account(context):
    c=context; entry=record(c).data
    RolePermission.objects.filter(role_code=c[4],permission__code='student_health.edit').delete()
    assert get(c).status_code == 200 and get(c).data['can_edit'] is False and record(c).status_code == 403
    foreign=School.objects.create(name='Other clinical school')
    family=Family.objects.create(school=foreign,family_name='Other clinical family')
    student=Student.objects.create(school=foreign,family=family,student_number='OTHER',first_name='Other',last_name='Patient',dob=date(2014,1,1))
    assert get(c,student_id=str(student.id)).status_code == 404
    assert c[5].get(URL,HTTP_X_SCHOOL_ID=str(foreign.id)).status_code == 404
    assert c[5].get(URL).status_code in {400,403}
    c[3].is_active=False; c[3].save(); assert get(c).status_code == 403


def test_inactive_patient_retains_history_and_allows_correction_only(context):
    c=context; entry=record(c).data; c[1].status='WITHDRAWN'; c[1].save()
    assert record(c).status_code == 400 and authorize(c).status_code == 400
    assert record(c,corrects_id=entry['entry_id']).status_code == 201
    assert get(c).data['entries_total'] == 2


def test_models_retain_identity_and_append_only_evidence(context):
    c=context; record(c); authorize(c)
    for model in (HealthEntry, MedicationAuthorization, HealthMutation):
        row=model.objects.first()
        with pytest.raises(ValidationError): row.delete()
        with pytest.raises(ValidationError): model.objects.all().delete()
        with pytest.raises(ValidationError): model.objects.all().update(school_id=uuid.uuid4())
        with pytest.raises(ValidationError): model.objects.bulk_update([], ['school'])
        with pytest.raises(ValidationError): model.objects.bulk_create([])
    with pytest.raises(ValidationError): HealthEntry.objects.first().save()
    with pytest.raises(ValidationError): HealthMutation.objects.first().save()
    order=MedicationAuthorization.objects.first(); order.dose=Decimal('2')
    with pytest.raises(ValidationError): order.save()


def test_full_chart_counts_pages_and_corrected_follow_up(context):
    c=context; today=timezone.localdate()
    for i in range(102):
        assert record(c,topic=f'Visit {i}',follow_up_on=today.isoformat()).status_code == 201
    first=get(c).data; second=get(c,offset=100,history_offset=100).data
    assert first['entries_total'] == 102 and len(first['entries']) == 100 and first['next_offset'] == 100
    assert first['summary'] == {'visit':102} and first['follow_up_due'] == 102
    assert len(second['entries']) == 2 and len(second['history']) == 2
    assert get(c,offset=-1).status_code == 400 and get(c,authorization_offset='bad').status_code == 400
    target=str(first['entries'][0]['id'])
    assert record(c,corrects_id=target,follow_up_on=(today+timedelta(days=2)).isoformat()).status_code == 201
    assert get(c).data['follow_up_due'] == 101


def test_seeded_clinical_roles_do_not_leak_to_generic_roles(context):
    from django.core.management import call_command
    from core.management.commands.seed_permissions import ROLE_PERMISSIONS
    c=context; call_command('seed_permissions', verbosity=0)
    for role in ('nurse', 'health', 'health_office', 'NURSE', 'HEALTH_OFFICE'):
        assert {'student_health.view','student_health.edit'} <= set(ROLE_PERMISSIONS[role])
        assert RolePermission.objects.filter(role_code=role,permission__code='student_health.view').exists()
    for role in ('ADMIN', 'SUPPORT', 'teacher', 'parent', 'student'):
        assert not RolePermission.objects.filter(role_code=role,permission__code__startswith='student_health.').exists()
        UserRole.objects.filter(user=c[3]).update(role_code=role)
        assert get(c).status_code == 403 and record(c).status_code == 403


def test_foreign_guardian_and_correction_cannot_expand_patient_scope(context):
    c=context; family=Family.objects.create(school=c[0],family_name='Other patient family')
    guardian=Guardian.objects.create(school=c[0],family=family,first_name='Other',last_name='Guardian',email='otherguardian@example.com',relationship='GUARDIAN')
    assert authorize(c,guardian_id=str(guardian.id)).status_code == 404
    other=Student.objects.create(school=c[0],family=family,student_number='DIFFERENT',first_name='Other',last_name='Student',dob=date(2014,1,1),status='ACTIVE')
    entry=record(c,student_id=str(other.id)).data
    assert record(c,corrects_id=entry['entry_id']).status_code == 404
    assert HealthEntry.objects.count() == 1 and not MedicationAuthorization.objects.exists()


def test_authorization_history_is_paginated_and_reachable(context):
    c=context
    for _ in range(101):
        assert authorize(c).status_code == 201
    first=get(c).data; second=get(c,authorization_offset=100).data
    assert first['authorizations_total'] == 101 and len(first['authorizations']) == 100
    assert first['authorizations_next_offset'] == 100
    assert len(second['authorizations']) == 1 and second['authorizations_next_offset'] is None
    assert not ({o['id'] for o in first['authorizations']} & {o['id'] for o in second['authorizations']})


def test_authorization_dates_use_school_timezone_at_utc_midnight(context, monkeypatch):
    from datetime import datetime, timezone as dt_timezone
    c=context; c[0].timezone='America/New_York'; c[0].save()
    monkeypatch.setattr(timezone,'now',lambda: datetime(2026,10,5,2,tzinfo=dt_timezone.utc))
    order=authorize(c,starts_on='2026-10-03',ends_on='2026-10-03').data
    assert record(c,kind='administration',authorization_id=order['authorization_id'],administration_state='not_given',occurred_at='2026-10-04T01:00:00Z',follow_up_on='2026-10-03').status_code == 201
    assert record(c,kind='administration',authorization_id=order['authorization_id'],administration_state='not_given',occurred_at='2026-10-04T06:00:00Z').status_code == 400
    assert get(c).data['follow_up_due'] == 1


def test_invalid_clinical_school_timezone_fails_closed(context):
    c=context; c[0].timezone='Invalid/School'; c[0].save()
    assert get(c).status_code == 400 and record(c).status_code == 400
