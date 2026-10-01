import uuid
from datetime import timedelta
import pytest
from django.utils import timezone
from rest_framework.test import APIClient
from core.models import UserAccount, UserRole
from academics.family_models import ClassroomFamilyThread, ClassroomFamilyMessage, ClassroomConferenceSlot, ClassroomDisclosure
from academics.tests.test_classroom_experience import classroom, get
from households.models import Guardian

pytestmark = pytest.mark.django_db
URL = '/api/v1/academics/classroom/family/'


def request(c, position=2, audience='parent', method='post', **data):
    client = APIClient(); client.force_authenticate(c[position])
    if method == 'get':
        return client.get(URL, {'audience': audience}, HTTP_X_SCHOOL_ID=str(c[0].id))
    return client.post(URL + '?audience=' + audience, {'request_key': str(uuid.uuid4()), **data}, format='json', HTTP_X_SCHOOL_ID=str(c[0].id))


def create(c, position=2, audience='parent', **data):
    guardian = Guardian.objects.get(account=c[2])
    return request(c, position, audience, operation='create', section_id=str(c[5].id), student_id=str(c[4].id), guardian_id=str(guardian.id),
                   title='Assignment question', content='What is the next step?', **data)


def test_conversation_context_and_resolution_are_audited(classroom):
    response = create(classroom, assignment_id=str(classroom[8].id))
    assert response.status_code == 200
    thread = ClassroomFamilyThread.objects.get()
    assert thread.assignment == classroom[8]
    assert request(classroom, 1, 'teacher', operation='reply', thread_id=str(thread.id), version=1, content='Here is the next step').status_code == 200
    assert request(classroom, operation='reply', thread_id=str(thread.id), version=1, content='Stale response').status_code == 409
    assert request(classroom, operation='resolve', thread_id=str(thread.id), version=2, content='Close it').status_code == 403
    assert request(classroom, 1, 'teacher', operation='resolve', thread_id=str(thread.id), version=2, content='Concern addressed; check again Friday').status_code == 200
    assert thread.messages.count() == 3
    assert request(classroom, 3, 'student', method='get').status_code == 403


def test_consent_requires_the_designated_guardian(classroom):
    assert create(classroom, kind='consent').status_code == 403
    assert create(classroom, 1, 'teacher', kind='consent').status_code == 200
    thread = ClassroomFamilyThread.objects.get()
    assert request(classroom, 1, 'teacher', operation='consent', thread_id=str(thread.id), version=1, decision='agreed', content='Staff agreement').status_code == 403
    assert request(classroom, operation='consent', thread_id=str(thread.id), version=1, decision='declined', content='Permission declined').status_code == 200
    thread.refresh_from_db(); assert thread.state == 'declined'
    assert thread.messages.last().decision == 'declined'


def test_conference_book_retry_collision_cancel_preserves_history(classroom):
    start = timezone.now() + timedelta(days=2); end = start + timedelta(minutes=20)
    args = dict(operation='slot', section_id=str(classroom[5].id), starts_at=start.isoformat(), ends_at=end.isoformat(), location='Classroom')
    assert request(classroom, 1, 'teacher', **args).status_code == 200
    assert request(classroom, 1, 'teacher', **args).status_code == 409
    slot = ClassroomConferenceSlot.objects.get()
    data = dict(operation='book', section_id=str(classroom[5].id), student_id=str(classroom[4].id), title='Conference', content='Discuss learning goals', slot_id=str(slot.id), request_key=str(uuid.uuid4()))
    assert request(classroom, **data).status_code == 200
    assert request(classroom, **data).status_code == 200
    data['request_key'] = str(uuid.uuid4())
    assert request(classroom, **data).status_code == 409
    thread = ClassroomFamilyThread.objects.get()
    assert request(classroom, operation='cancel', thread_id=str(thread.id), version=1, content='Please schedule another time').status_code == 200
    slot.refresh_from_db(); assert slot.state == 'cancelled'
    assert thread.messages.count() == 2


def test_restricted_guardian_loses_all_classroom_family_access(classroom):
    create(classroom)
    leader = UserAccount.objects.create_user(username='leader-family', school=classroom[0]); UserRole.objects.create(user=leader, school=classroom[0], role_code='ADMIN')
    c = list(classroom); c[1] = leader
    guardian = Guardian.objects.get(account=classroom[2])
    args = dict(operation='disclosure', student_id=str(classroom[4].id), guardian_id=str(guardian.id), allowed=False, reason='School verified disclosure restriction')
    assert request(classroom, 1, 'teacher', **args).status_code == 403
    assert request(c, 1, 'admin', **args).status_code == 200
    assert ClassroomDisclosure.objects.get().updated_by == leader
    assert get(classroom[2], classroom[0], audience='parent').status_code == 403
    assert request(classroom, method='get').status_code == 403
    assert get(classroom[3], classroom[0], audience='student').status_code == 200


def test_other_guardian_cannot_read_private_thread(classroom):
    create(classroom)
    account = UserAccount.objects.create_user(username='other-guardian', school=classroom[0])
    Guardian.objects.create(school_id=classroom[0].id, household=classroom[4].household, account=account, first_name='Other', last_name='Guardian')
    c = list(classroom); c[2] = account
    assert request(c, method='get').data['threads'] == []
    thread = ClassroomFamilyThread.objects.get()
    assert request(c, operation='reply', thread_id=str(thread.id), version=1, content='Unauthorized reply').status_code == 404


def test_preferences_validate_timezone_and_digest_uses_published_evidence(classroom):
    args = dict(operation='preferences', in_app=True, digest_day=4, timezone='America/New_York', quiet_start='21:00', quiet_end='07:00')
    assert request(classroom, **args).status_code == 200
    args['timezone'] = 'Invalid/Zone'; assert request(classroom, **args).status_code == 400
    data = request(classroom, method='get').data
    assert data['preferences']['timezone'] == 'America/New_York'
    assert data['digest']['assignments'][0]['id'] == classroom[8].id
    assert data['digest']['recorded_submissions'] == 0
    assert data['digest']['delivery'] == 'in_app'


def test_message_evidence_cannot_be_changed_or_deleted(classroom):
    from django.core.exceptions import ValidationError
    create(classroom)
    message = ClassroomFamilyMessage.objects.get()
    with pytest.raises(ValidationError): message.save()
    with pytest.raises(ValidationError): message.delete()
    with pytest.raises(ValidationError): ClassroomFamilyMessage.objects.all().delete()


def test_retry_key_is_bound_to_content(classroom):
    key = str(uuid.uuid4())
    assert create(classroom, request_key=key).status_code == 200
    assert create(classroom, request_key=key).status_code == 200
    assert create(classroom, request_key=key, assignment_id=str(classroom[8].id)).status_code == 409
    assert ClassroomFamilyThread.objects.count() == 1


def test_quiet_hours_and_source_keys_delay_and_deduplicate_in_app_notices(classroom):
    from datetime import datetime, timezone as dt_timezone
    from academics.family_models import ClassroomNotificationPreference, ClassroomFamilyNotice
    from academics.family_notifications import queue_notice, prepare_digests
    school, _, parent, *_ = classroom
    ClassroomNotificationPreference.objects.create(school_id=school.id, account=parent, in_app=True, digest_day=3,
                  timezone='UTC', quiet_start='21:00', quiet_end='07:00')
    preference = ClassroomNotificationPreference.objects.get(); preference.refresh_from_db()
    now = datetime(2026, 10, 1, 22, 0, tzinfo=dt_timezone.utc)
    first = queue_notice(school.id, parent, 'message:1', 'Classroom update', now=now)
    second = queue_notice(school.id, parent, 'message:1', 'Classroom update', now=now)
    assert first.id == second.id
    assert first.available_at == datetime(2026, 10, 2, 7, 0, tzinfo=dt_timezone.utc)
    assert prepare_digests(now) == 1
    assert prepare_digests(now) == 0
    assert ClassroomFamilyNotice.objects.count() == 2
    preference.in_app = False; preference.save()
    assert queue_notice(school.id, parent, 'message:2', 'Update', now=now) is None


def test_disabled_preferences_and_restrictions_hide_notices(classroom):
    from academics.family_models import ClassroomFamilyNotice
    create(classroom, 1, 'teacher')
    assert request(classroom, method='get').data['notices']
    args = dict(operation='preferences', in_app=False, digest_day=0, timezone='UTC')
    assert request(classroom, **args).status_code == 200
    assert request(classroom, method='get').data['notices'] == []
    assert ClassroomFamilyNotice.objects.count() == 1


def test_replay_cannot_disclose_restricted_child_when_sibling_remains_authorized(classroom):
    from households.models import Student
    from academics.models import Enrollment
    c=classroom
    sibling=Student.objects.create(school_id=c[0].id,household=c[4].household,first_name='Sibling',last_name='One')
    Enrollment.objects.create(school_id=c[0].id,section=c[5],student=sibling)
    client=APIClient();client.force_authenticate(c[2])
    payload={'operation':'create','section_id':str(c[5].id),'student_id':str(c[4].id),'kind':'conversation','title':'Private child concern','content':'Restricted child information','request_key':str(uuid.uuid4())}
    endpoint='/api/v1/academics/classroom/family/?audience=parent'
    assert client.post(endpoint,payload,format='json',HTTP_X_SCHOOL_ID=str(c[0].id)).status_code==200
    guardian=Guardian.objects.get(account=c[2])
    ClassroomDisclosure.objects.create(school_id=c[0].id,student=c[4],guardian=guardian,allowed=False,reason='School restriction',updated_by=c[1])
    assert client.get(endpoint,HTTP_X_SCHOOL_ID=str(c[0].id)).status_code==200
    replay=client.post(endpoint,payload,format='json',HTTP_X_SCHOOL_ID=str(c[0].id))
    assert replay.status_code==404
    assert 'Restricted child information' not in str(replay.data)
