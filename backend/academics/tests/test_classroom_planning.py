import uuid
from datetime import timedelta
import pytest
from django.utils import timezone
from rest_framework.test import APIClient
from academics.tests.test_classroom_experience import classroom
from academics.models import Enrollment
from academics.planning_models import ClassroomSectionPlanning, ClassroomPlanningEvent
from academics.support_models import ClassroomInterventionLink
from signals.models import InterventionCase
from core.models import UserAccount, UserRole

pytestmark=pytest.mark.django_db


def post(c, client, endpoint='planning', **data):
    return client.post('/api/v1/academics/classroom/'+endpoint+'/?audience=admin',{'section_id':str(c[5].id),'request_key':str(uuid.uuid4()),**data},format='json',HTTP_X_SCHOOL_ID=str(c[0].id))


def leader(c):
    user=UserAccount.objects.create_user(username='planning-leader',email='planning-leader@example.com',school=c[0]);UserRole.objects.create(user=user,school=c[0],role_code='ADMIN')
    client=APIClient();client.force_authenticate(user);return client


def test_planning_target_versions_retries_and_immutable_history(classroom):
    c=classroom; client=leader(c)
    data={'target_size':24,'planning_note':'Allow small-group work','version':0,'request_key':str(uuid.uuid4())}
    assert post(c,client,**data).status_code==200
    assert post(c,client,**data).status_code==200
    assert ClassroomPlanningEvent.objects.count()==1
    assert post(c,client,**{**data,'target_size':25}).status_code==409
    assert post(c,client,target_size=25,planning_note='Review room capacity',version=0).status_code==409
    assert post(c,client,target_size=25,planning_note='Review room capacity',version=1).status_code==200
    assert ClassroomSectionPlanning.objects.get().version==2
    assert Enrollment.objects.count()==1
    from django.core.exceptions import ValidationError
    with pytest.raises(ValidationError): ClassroomPlanningEvent.objects.all().update(payload={})


def test_planning_rejects_nonleader_and_boolean_target(classroom):
    c=classroom
    client=APIClient();client.force_authenticate(c[1])
    assert post(c,client,target_size=20,planning_note='Room planning',version=0).status_code==403
    assert post(c,leader(c),target_size=True,planning_note='Room planning',version=0).status_code==400


def test_owner_reassignment_preserves_legacy_id_and_linked_case(classroom):
    c=classroom; client=leader(c)
    case=InterventionCase.objects.create(school_id=c[0].id,student=c[4],reason='Legacy support',owner_user_id=77)
    data={'operation':'assign_case','case_id':str(case.id),'owner_id':str(c[1].id),'version':1,'note':'Assign classroom follow-through','review_at':(timezone.now()+timedelta(days=7)).isoformat()}
    assert post(c,client,'support',**data).status_code==200
    case.refresh_from_db()
    assert case.owner_account==c[1] and case.owner_user_id==77 and case.version==2
    assert ClassroomInterventionLink.objects.get().case==case
    assert case.actions.get().created_by_account is not None
    assert post(c,client,'support',**data).status_code==409
    data['version']=2;data['owner_id']=str(c[2].id)
    assert post(c,client,'support',**data).status_code==400
    case.refresh_from_db();assert case.owner_account==c[1] and case.version==2


def test_board_report_does_not_disclose_planning_rationale(classroom):
    c=classroom;client=leader(c)
    post(c,client,target_size=20,planning_note='Private staffing rationale',version=0)
    user=UserAccount.objects.create_user(username='planning-board',email='planning-board@example.com',school=c[0]);UserRole.objects.create(user=user,school=c[0],role_code='BOARD')
    client.force_authenticate(user)
    r=client.get('/api/v1/academics/classroom/leadership/',{'audience':'board'},HTTP_X_SCHOOL_ID=str(c[0].id))
    assert r.status_code==200
    assert 'Private staffing rationale' not in str(r.data)
    assert r.data['summary']['recorded_attendance_rows']==0


def test_attendance_report_uses_canonical_verified_records(classroom):
    from academics.tests.test_classroom_operations import identity, request
    c=classroom;identity(c)
    assert request(c,operation='attendance',version=0,items=[{'student_id':str(c[4].id),'status':'ABSENT'}],reason='Roll call confirmed').status_code==200
    client=leader(c)
    r=client.get('/api/v1/academics/classroom/leadership/',{'audience':'admin'},HTTP_X_SCHOOL_ID=str(c[0].id))
    assert r.status_code==200
    assert r.data['summary']['recorded_attendance_rows']==r.data['summary']['recorded_absences']==1
    assert 'attendance_percentage' not in r.data['summary']
