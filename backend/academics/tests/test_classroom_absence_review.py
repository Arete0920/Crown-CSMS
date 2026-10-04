import uuid
from datetime import timedelta
import pytest
from django.utils import timezone
from rest_framework.test import APIClient
from academics.tests.test_classroom_experience import classroom
from academics.tests.test_classroom_operations import identity, request
from academics.collaboration_models import ClassroomRecord, ClassroomEvent
from academics.operations_models import ClassroomAttendanceAudit, ClassroomAttendanceSession, ClassroomSubstituteGrant
from core.models import School, UserAccount, UserRole
from crown_api.models import AttendanceRecord

pytestmark = pytest.mark.django_db


def explanation(c, *, dated=True):
    return ClassroomRecord.objects.create(school_id=c[0].id, section=c[5], student=c[4],
        kind='absence_explanation', title='Family explanation', body='Family supplied explanation',
        visibility='family', owner=c[2], created_by=c[2], request_key=uuid.uuid4(), fingerprint='fixture',
        metadata={'absence_date': timezone.localdate().isoformat()} if dated else {})


def prepare(c, *, dated=True):
    core = identity(c)
    AttendanceRecord.objects.create(student=core, section=c[5], date=timezone.localdate(), status='ABSENT')
    return explanation(c, dated=dated)


def review(c, record, **extra):
    return request(c, operation='review_absence', explanation_id=str(record.id),
        explanation_version=record.version, version=0, decision='excuse',
        reason='Reviewed school absence policy', **extra)


def test_parent_explanation_is_dated_and_never_writes_official_attendance(classroom):
    c = classroom
    client = APIClient(); client.force_authenticate(c[2])
    payload = {'kind': 'absence_explanation', 'section_id': str(c[5].id), 'student_id': str(c[4].id),
        'title': 'Absence', 'body': 'Explanation', 'request_key': str(uuid.uuid4()),
        'metadata': {'absence_date': timezone.localdate().isoformat()}}
    response = client.post('/api/v1/academics/classroom/records/?audience=parent', payload,
        format='json', HTTP_X_SCHOOL_ID=str(c[0].id))
    assert response.status_code == 201
    assert response.data['metadata'] == payload['metadata']
    assert not AttendanceRecord.objects.exists()
    payload['request_key'] = str(uuid.uuid4())
    payload['metadata']['absence_date'] = (timezone.localdate() + timedelta(days=1)).isoformat()
    assert client.post('/api/v1/academics/classroom/records/?audience=parent', payload,
        format='json', HTTP_X_SCHOOL_ID=str(c[0].id)).status_code == 400


def test_review_atomically_updates_canonical_attendance_and_both_histories(classroom):
    c = classroom; record = prepare(c)
    key = str(uuid.uuid4())
    assert review(c, record, request_key=key).status_code == 200
    assert review(c, record, request_key=key).status_code == 200
    assert AttendanceRecord.objects.get().status == 'EXCUSED'
    record.refresh_from_db(); assert record.state == 'resolved' and record.version == 2
    assert ClassroomAttendanceAudit.objects.count() == ClassroomEvent.objects.count() == 1
    assert ClassroomAttendanceAudit.objects.get().changes[0]['explanation_id'] == str(record.id)
    assert ClassroomEvent.objects.get().payload['before'] == 'ABSENT'
    assert not request(c, method='get').data['absence_explanations']
    client = APIClient(); client.force_authenticate(c[2])
    family = client.get('/api/v1/academics/classroom/records/?audience=parent', HTTP_X_SCHOOL_ID=str(c[0].id))
    assert family.data['records'][0]['history'][0]['payload']['decision'] == 'excuse'


def test_decline_retains_official_status_and_records_review(classroom):
    c = classroom; record = prepare(c)
    response = request(c, operation='review_absence', explanation_id=str(record.id),
        explanation_version=1, version=0, decision='decline', reason='School policy reviewed')
    assert response.status_code == 200
    assert AttendanceRecord.objects.get().status == 'ABSENT'
    assert ClassroomAttendanceAudit.objects.get().changes[0]['decision'] == 'decline'


@pytest.mark.parametrize('status', ['PRESENT', 'TARDY', None])
def test_review_cannot_invent_or_override_a_nonabsence(classroom, status):
    c = classroom; record = prepare(c)
    if status:
        row = AttendanceRecord.objects.get(); row.status = status; row.save()
    else:
        AttendanceRecord.objects.all().delete()
    assert review(c, record).status_code in {404, 409}
    record.refresh_from_db(); assert record.state == 'open' and record.version == 1
    assert not ClassroomAttendanceAudit.objects.exists() and not ClassroomEvent.objects.exists()


def test_stale_versions_and_wrong_date_do_not_partially_save(classroom):
    c = classroom; record = prepare(c)
    record.version = 2
    assert review(c, record).status_code == 409
    record.version = 1
    assert review(c, record, date=(timezone.localdate() - timedelta(days=1)).isoformat()).status_code == 400
    assert not ClassroomAttendanceAudit.objects.exists()
    assert AttendanceRecord.objects.get().status == 'ABSENT'
    ClassroomAttendanceSession.objects.create(school_id=c[0].id, section=c[5], date=timezone.localdate(), version=1)
    assert review(c, record).status_code == 409


def test_undated_legacy_explanation_requires_explicit_date_confirmation(classroom):
    c = classroom; record = prepare(c, dated=False)
    assert review(c, record).status_code == 400
    assert review(c, record, confirm_undated_date=True).status_code == 200
    assert ClassroomEvent.objects.get().payload['date'] == timezone.localdate().isoformat()


def test_parent_substitute_and_cross_school_review_are_denied(classroom):
    c = classroom; record = prepare(c)
    substitute = UserAccount.objects.create_user(username='absence-substitute', school=c[0])
    UserRole.objects.create(user=substitute, school=c[0], role_code='TEACHER')
    now = timezone.now()
    ClassroomSubstituteGrant.objects.create(school_id=c[0].id, section=c[5], account=substitute,
        granted_by=c[1], starts_at=now-timedelta(minutes=1), expires_at=now+timedelta(hours=1), instructions='Roster only')
    for user in (c[2], substitute):
        context = list(c); context[1] = user
        assert review(context, record).status_code == 403
    context = list(c); context[1] = substitute
    data = request(context, method='get').data
    assert data['can_review_absences'] is False and data['absence_explanations'] == []
    record.school_id = School.objects.create(name='Other absence tenant').id; record.save()
    assert review(c, record).status_code == 404
    assert AttendanceRecord.objects.get().status == 'ABSENT'


def test_unverified_identity_and_invalid_reason_fail_closed(classroom):
    c = classroom; record = explanation(c)
    assert review(c, record).status_code == 404
    identity(c)
    assert request(c, operation='review_absence', explanation_id=str(record.id),
        explanation_version=1, version=0, decision='excuse', reason='').status_code == 400


def test_queue_excludes_other_dates_and_inactive_children(classroom):
    c = classroom; record = explanation(c)
    assert len(request(c, method='get').data['absence_explanations']) == 1
    record.metadata = {'absence_date': (timezone.localdate()-timedelta(days=1)).isoformat()}; record.save()
    assert request(c, method='get').data['absence_explanations'] == []
    record.metadata = {}; record.save(); c[4].is_active = False; c[4].save()
    assert request(c, method='get').data['absence_explanations'] == []
