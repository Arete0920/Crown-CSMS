import uuid
import pytest
from django.core.exceptions import ValidationError
from rest_framework.test import APIClient
from academics.collaboration_models import ClassroomRecord, ClassroomEvent
from academics.tests.test_classroom_experience import classroom
from core.models import UserAccount
from households.models import Student
from academics.models import Enrollment

pytestmark = pytest.mark.django_db
URL = '/api/v1/academics/classroom/records/'


def client_for(c, position):
    client = APIClient(); client.force_authenticate(c[position]); return client


def create(c, position=1, audience='teacher', **extra):
    return client_for(c, position).post(URL + '?audience=' + audience, {
        'kind': 'announcement', 'section_id': str(c[5].id), 'title': 'Classroom record',
        'body': 'Evidence and next step', 'request_key': str(uuid.uuid4()), **extra,
    }, format='json', HTTP_X_SCHOOL_ID=str(c[0].id))


def listing(c, position, audience):
    return client_for(c, position).get(URL, {'audience': audience}, HTTP_X_SCHOOL_ID=str(c[0].id))


def action(c, record, position=1, audience='teacher', **extra):
    return client_for(c, position).post(f'{URL}{record.id}/actions/?audience={audience}', {
        'action': 'acknowledge', 'note': 'Reviewed; next step assigned', 'version': record.version,
        'request_key': str(uuid.uuid4()), **extra,
    }, format='json', HTTP_X_SCHOOL_ID=str(c[0].id))


def test_help_is_private_from_family_and_has_accountable_follow_through(classroom):
    assert create(classroom, 3, 'student', kind='help_request', student_id=str(classroom[4].id)).status_code == 201
    record = ClassroomRecord.objects.get()
    assert record.owner == classroom[1]
    assert len(listing(classroom, 1, 'teacher').data['records']) == 1
    assert listing(classroom, 2, 'parent').data['records'] == []
    assert action(classroom, record).status_code == 200
    record.refresh_from_db()
    assert action(classroom, record, action='resolve').data['state'] == 'resolved'
    assert len(listing(classroom, 3, 'student').data['records'][0]['history']) == 2


def test_private_reflection_remains_private_and_board_cannot_read(classroom):
    assert create(classroom, 3, 'student', kind='reflection', visibility='private', student_id=str(classroom[4].id)).status_code == 201
    assert listing(classroom, 1, 'teacher').data['records'] == []
    assert listing(classroom, 2, 'parent').data['records'] == []
    assert len(listing(classroom, 3, 'student').data['records']) == 1
    assert listing(classroom, 1, 'board').status_code == 403


def test_response_answers_and_history_never_leak_to_peer(classroom):
    create(classroom, kind='formative_check', metadata={'questions': ['What is your evidence?']})
    record = ClassroomRecord.objects.get()
    assert action(classroom, record, 3, 'student', action='respond', student_id=str(classroom[4].id), content='Private answer').status_code == 200
    peer = UserAccount.objects.create_user(username='peer', school=classroom[0])
    other = Student.objects.create(school_id=classroom[0].id, household=classroom[4].household, account=peer, first_name='Peer', last_name='Student')
    Enrollment.objects.create(school_id=classroom[0].id, section=classroom[5], student=other)
    client = APIClient(); client.force_authenticate(peer)
    data = client.get(URL, {'audience': 'student'}, HTTP_X_SCHOOL_ID=str(classroom[0].id)).data['records'][0]
    assert data['responses'] == []
    assert data['history'] == []
    record.refresh_from_db()
    response = record.responses.get()
    assert action(classroom, record, action='feedback', response_id=str(response.id), note='Explain the observation').status_code == 200
    own = listing(classroom, 3, 'student').data['records'][0]
    assert own['responses'][0]['feedback'] == 'Explain the observation'


def test_retry_conflict_and_stale_version_preserve_evidence(classroom):
    key = str(uuid.uuid4())
    assert create(classroom, request_key=key).status_code == 201
    assert create(classroom, request_key=key).status_code == 200
    assert create(classroom, request_key=key, body='Different').status_code == 409
    record = ClassroomRecord.objects.get()
    key = str(uuid.uuid4())
    assert action(classroom, record, request_key=key).status_code == 200
    assert action(classroom, record, request_key=key).status_code == 200
    assert action(classroom, record).status_code == 409
    event = ClassroomEvent.objects.get()
    with pytest.raises(ValidationError): event.delete()
    with pytest.raises(ValidationError): event.save()
    with pytest.raises(ValidationError): ClassroomEvent.objects.all().update(action='resolve')


@pytest.mark.parametrize('extra', [{'kind': 'formative_check'}, {'kind': 'group_project', 'metadata': {'members': [str(uuid.uuid4())]}}, {'kind': 'goal', 'student_id': 'bad'}, {'metadata': {'score': 100}}, {'kind': 'resource', 'metadata': {'reference': 'javascript:alert(1)'}}])
def test_invalid_classroom_records_do_not_mutate(classroom, extra):
    assert create(classroom, **extra).status_code in {400, 404}
    assert not ClassroomRecord.objects.exists()


def test_parents_may_explain_absence_but_cannot_create_teaching_records(classroom):
    assert create(classroom, 2, 'parent').status_code == 403
    assert create(classroom, 2, 'parent', kind='absence_explanation', student_id=str(classroom[4].id)).status_code == 201
    record = ClassroomRecord.objects.get()
    assert action(classroom, record, 2, 'parent', action='resolve').status_code == 403


def test_support_requires_review_date_and_family_disclosure_is_deliberate(classroom):
    assert create(classroom, kind='support_plan', student_id=str(classroom[4].id)).status_code == 400
    assert create(classroom, kind='support_plan', student_id=str(classroom[4].id), due_at='2026-10-10T12:00:00Z', visibility='family').status_code == 201
    assert listing(classroom, 2, 'parent').data['records'] == []


def test_portfolio_links_canonical_published_work(classroom):
    assert create(classroom, 3, 'student', kind='portfolio', student_id=str(classroom[4].id), metadata={'assignment_id': str(classroom[8].id)}, visibility='family').status_code == 201
    assert listing(classroom, 2, 'parent').data['records'][0]['metadata']['assignment_id'] == str(classroom[8].id)


def test_group_members_must_be_enrolled_and_only_members_respond(classroom):
    assert create(classroom, kind='group_project', metadata={'members': [str(classroom[4].id)], 'roles': {str(classroom[4].id): 'Recorder'}, 'milestones': ['Observe']}).status_code == 201
    record = ClassroomRecord.objects.get()
    assert action(classroom, record, 3, 'student', action='respond', student_id=str(classroom[4].id), content='Recorded the observations').status_code == 200
    record.refresh_from_db()
    assert action(classroom, record, 2, 'parent', action='respond', student_id=str(classroom[4].id), content='Parent answer').status_code == 403
