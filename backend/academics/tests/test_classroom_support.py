import uuid
from datetime import timedelta
import pytest
from django.utils import timezone
from rest_framework.test import APIClient
from academics.tests.test_classroom_experience import classroom
from academics.tests.test_classroom_operations import identity
from academics.support_models import ClassroomInterventionLink, ClassroomRestorativeLink
from signals.models import InterventionCase, InterventionAction
from discipline.models import DisciplineIncident, DisciplineAction

pytestmark=pytest.mark.django_db
URL='/api/v1/academics/classroom/support/'


def request(c, position=1, audience='teacher', method='post', **data):
    client=APIClient(); client.force_authenticate(c[position])
    if method=='get': return client.get(URL, {'audience':audience}, HTTP_X_SCHOOL_ID=str(c[0].id))
    payload={'section_id':str(c[5].id),'request_key':str(uuid.uuid4()),**data}
    return client.post(URL+'?audience='+audience,payload,format='json',HTTP_X_SCHOOL_ID=str(c[0].id))


def case_args(c):
    return {'operation':'case','student_id':str(c[4].id),'title':'Observation support','note':'Practice identifying evidence with weekly feedback','review_at':(timezone.now()+timedelta(days=7)).isoformat()}


def test_instructional_support_uses_canonical_case_uuid_owner_and_review(classroom):
    args=case_args(classroom); args['request_key']=str(uuid.uuid4())
    assert request(classroom,**args).status_code==200
    assert request(classroom,**args).status_code==200
    case=InterventionCase.objects.get()
    assert case.owner_account==classroom[1]
    assert case.owner_user_id is None
    assert ClassroomInterventionLink.objects.get().case==case
    assert case.actions.get().created_by_account==classroom[1]
    args={'operation':'follow_up','case_id':str(case.id),'version':1,'note':'Student explained one observation independently','review_at':(timezone.now()+timedelta(days=7)).isoformat()}
    assert request(classroom,**args).status_code==200
    assert request(classroom,**args).status_code==409
    assert request(classroom,operation='close_case',case_id=str(case.id),version=2,note='Independent explanation confirmed; maintain ordinary classroom support').status_code==200
    case.refresh_from_db(); assert case.status=='CLOSED'; assert case.closed_at
    assert case.actions.count()==3


def test_family_cannot_read_confidential_support_case(classroom):
    request(classroom,**case_args(classroom))
    assert request(classroom,2,'parent',method='get').status_code==403
    assert request(classroom,3,'student',method='get').status_code==403


def test_restorative_follow_through_uses_verified_identity_and_canonical_discipline(classroom):
    data=case_args(classroom); data['operation']='restorative'; data['title']='Restore classroom participation'
    assert request(classroom,**data).status_code==404
    assert not DisciplineIncident.objects.exists()
    core=identity(classroom)
    assert request(classroom,**data).status_code==200
    incident=DisciplineIncident.objects.get(); link=ClassroomRestorativeLink.objects.get()
    assert incident.student==core
    assert link.student==classroom[4]
    assert not incident.parent_notified
    assert request(classroom,operation='restorative_note',incident_id=str(incident.id),version=1,note='Repair conversation completed; observe the next lesson',review_at=(timezone.now()+timedelta(days=2)).isoformat()).status_code==200
    assert request(classroom,operation='close_restorative',incident_id=str(incident.id),version=2,note='Repair commitments completed and participation restored').status_code==200
    assert incident.actions.count()==3


def test_support_actions_are_append_only(classroom):
    from django.core.exceptions import ValidationError
    request(classroom,**case_args(classroom))
    action=InterventionAction.objects.get()
    with pytest.raises(ValidationError): action.save()
    with pytest.raises(ValidationError): action.delete()
    with pytest.raises(ValidationError): InterventionAction.objects.all().update(note='Rewrite')


def test_legacy_signals_api_does_not_disclose_cases_to_guardians_or_allow_actor_spoofing(classroom):
    request(classroom,**case_args(classroom))
    case=InterventionCase.objects.get()
    client=APIClient();client.force_authenticate(classroom[2])
    assert client.get('/api/v1/signals/interventions/cases/',HTTP_X_SCHOOL_ID=str(classroom[0].id)).status_code==403
    client.force_authenticate(classroom[1])
    assert client.get('/api/v1/signals/board/risk-counts/',HTTP_X_SCHOOL_ID=str(classroom[0].id)).status_code==403
    response=client.post(f'/api/v1/signals/interventions/cases/{case.id}/actions/',{'note':'Verified follow-up','created_by_user_id':123},format='json',HTTP_X_SCHOOL_ID=str(classroom[0].id))
    assert response.status_code==201
    latest=case.actions.order_by('created_at').last()
    assert latest.created_by_account==classroom[1]
    assert latest.created_by_user_id is None
    case.refresh_from_db(); assert case.version==2


def test_support_owner_must_be_authorized_for_classroom(classroom):
    data=case_args(classroom);data['owner_id']=str(classroom[2].id)
    assert request(classroom,**data).status_code==400
    assert not InterventionCase.objects.exists()
