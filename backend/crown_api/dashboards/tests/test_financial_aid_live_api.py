"""School-scoped live Jireh dashboard API integration tests (requires Django/DRF)."""
from datetime import date
import pytest
from django.test import override_settings
from rest_framework.test import APIClient
from aid.models import AidApplication, AidAward
from core.models import AcademicYear, CrownPermission, Family, RolePermission, School, Student, UserAccount, UserRole

URL = '/api/v1/dashboards/financial-aid/summary'

def records(name):
    school = School.objects.create(name=name)
    year = AcademicYear.objects.create(school=school,name='2026-2027',
        start_date=date(2026,8,1),end_date=date(2027,6,30),is_current=True)
    family = Family.objects.create(school=school,family_name=f'{name} Family')
    student = Student.objects.create(school=school,family=family,student_number=f'{name}-1',
        first_name='Test',last_name='Student',dob=date(2014,1,1))
    app = AidApplication.objects.create(school=school,academic_year=year,family=family,
        status=AidApplication.STATUS_SUBMITTED)
    AidAward.objects.create(school=school,academic_year=year,student=student,
        aid_application=app,awarded_cents=12500,decision_status=AidAward.DECISION_ACCEPTED)
    return school,year,app

def client_for(school, granted=True):
    user = UserAccount.objects.create_user(username=f'fa-{school.id}-{granted}',
        email=f'fa-{school.id}-{granted}@example.org',password='test-only',school=school)
    if granted:
        permission,_ = CrownPermission.objects.get_or_create(code='financial_aid.view')
        RolePermission.objects.get_or_create(role_code='AID_DIRECTOR',permission=permission)
        UserRole.objects.get_or_create(user=user,school=school,role_code='AID_DIRECTOR')
    client = APIClient()
    client.force_authenticate(user=user)
    return client

@pytest.mark.django_db
@override_settings(CROWN_DEV_OPEN_API=False,TENANT_HEADER_REQUIRED=True)
def test_current_year_live_records_are_scoped_and_amounts_are_not_disbursements():
    a,_,_ = records('A')
    records('B')
    r = client_for(a).get(URL,HTTP_X_SCHOOL_ID=str(a.id))
    assert r.status_code == 200, r.content
    data=r.json()
    metrics={m['label']:m['value'] for m in data['metrics']}
    assert metrics['Applications submitted (current year)']=='1'
    assert metrics['Accepted award records']=='1'
    assert metrics['Accepted award face value']=='$125.00'
    assert data['meta']['served_from']=='live_db'
    assert data['meta']['money_basis']=='face_value_not_disbursement'
    assert data['meta']['school_id']==str(a.id)
    assert 'B Family' not in str(data)

@pytest.mark.django_db
@override_settings(CROWN_DEV_OPEN_API=False,TENANT_HEADER_REQUIRED=True)
def test_missing_school_financial_aid_grant_is_denied():
    s,_,_=records('Denied')
    assert client_for(s,False).get(URL,HTTP_X_SCHOOL_ID=str(s.id)).status_code==403

@pytest.mark.django_db
@override_settings(CROWN_DEV_OPEN_API=False,TENANT_HEADER_REQUIRED=True)
def test_cross_school_header_cannot_read_financial_aid():
    a,_,_=records('East')
    b,_,_=records('West')
    r=client_for(a).get(URL,HTTP_X_SCHOOL_ID=str(b.id))
    assert r.status_code in (403,404)
    assert 'West Family' not in str(r.content)

@pytest.mark.django_db
@override_settings(CROWN_DEV_OPEN_API=False,TENANT_HEADER_REQUIRED=True)
def test_multiple_current_academic_years_do_not_return_partial_totals():
    s,_,_=records('Duplicate')
    AcademicYear.objects.create(school=s,name='2027-2028',
        start_date=date(2027,8,1),end_date=date(2028,6,30),is_current=True)
    r=client_for(s).get(URL,HTTP_X_SCHOOL_ID=str(s.id))
    assert r.status_code==503
    assert r.json()['code']=='financial_aid_integrity_review_required'
    assert 'metrics' not in r.json()

@pytest.mark.django_db
@override_settings(CROWN_DEV_OPEN_API=False,TENANT_HEADER_REQUIRED=True)
def test_cross_school_family_relation_requires_integrity_review():
    a,_,app=records('Mismatch-A')
    b,_,_=records('Mismatch-B')
    family=Family.objects.filter(school=b).first()
    app.family=family
    app.save(update_fields=['family'])
    r=client_for(a).get(URL,HTTP_X_SCHOOL_ID=str(a.id))
    assert r.status_code==503
    assert r.json()['code']=='financial_aid_integrity_review_required'
    assert 'metrics' not in r.json()
