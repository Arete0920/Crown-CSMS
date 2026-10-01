import uuid
from datetime import timedelta
import pytest
from django.utils import timezone
from rest_framework.test import APIClient
from academics.tests.test_classroom_experience import classroom
from core.models import Family, Student as CoreStudent, StudentIdentityLink, UserAccount, UserRole
from academics.operations_models import ClassroomAttendanceSession, ClassroomAttendanceAudit, ClassroomSubstituteGrant, ClassroomEmergencySession
from crown_api.models import AttendanceRecord

pytestmark = pytest.mark.django_db
URL = '/api/v1/academics/classroom/operations/'


def request(c, method='post', **payload):
    client = APIClient(); client.force_authenticate(c[1])
    data = {'section_id': str(c[5].id), 'date': timezone.localdate().isoformat(), **payload}
    if method == 'get':
        return client.get(URL, data, HTTP_X_SCHOOL_ID=str(c[0].id))
    return client.post(URL, {'request_key': str(uuid.uuid4()), **data}, format='json', HTTP_X_SCHOOL_ID=str(c[0].id))


def identity(c):
    family = Family.objects.create(school=c[0], family_name='Classroom core family')
    core = CoreStudent.objects.create(school=c[0], family=family, student_number='CLASS-1', dob='2012-01-01', first_name='Student', last_name='One')
    StudentIdentityLink.objects.create(school=c[0], core_student=core, compatibility_student=c[4], source='manual', evidence_reference='School verified roster identity')
    return core


def test_attendance_requires_verified_identity_and_preserves_correction_history(classroom):
    data = {'operation': 'attendance', 'version': 0, 'items': [{'student_id': str(classroom[4].id), 'status': 'PRESENT'}], 'reason': 'Confirmed during roll call'}
    assert request(classroom, **data).status_code == 404
    assert not AttendanceRecord.objects.exists()
    core = identity(classroom)
    key = str(uuid.uuid4())
    assert request(classroom, request_key=key, **data).status_code == 200
    assert request(classroom, request_key=key, **data).status_code == 200
    assert AttendanceRecord.objects.get().student == core
    assert ClassroomAttendanceAudit.objects.count() == 1
    data['items'][0]['status'] = 'TARDY'
    assert request(classroom, **data).status_code == 409
    data['version'] = 1; data['reason'] = 'Arrived after roll call'
    assert request(classroom, **data).status_code == 200
    evidence = ClassroomAttendanceAudit.objects.order_by('version').last()
    assert evidence.changes[0]['before'] == 'PRESENT'
    assert evidence.changes[0]['after'] == 'TARDY'
    assert ClassroomAttendanceSession.objects.get().version == 2


def test_legacy_attendance_writer_also_appends_evidence(classroom):
    identity(classroom)
    client = APIClient(); client.force_authenticate(classroom[1])
    response = client.post(f'/api/v1/academics/sections/{classroom[5].id}/attendance/', {'items': [{'student_id': str(classroom[4].id), 'status': 'PRESENT'}]}, format='json', HTTP_X_SCHOOL_ID=str(classroom[0].id))
    assert response.status_code == 200
    assert ClassroomAttendanceAudit.objects.get().changes[0]['before'] is None


def test_substitute_grant_expires_and_cannot_redelegate(classroom):
    substitute = UserAccount.objects.create_user(username='substitute', school=classroom[0])
    UserRole.objects.create(user=substitute, school=classroom[0], role_code='TEACHER')
    now = timezone.now()
    assert request(classroom, operation='grant', account_id=str(substitute.id), starts_at=(now-timedelta(minutes=1)).isoformat(), expires_at=(now+timedelta(hours=3)).isoformat(), instructions='Teach the published plan; report follow-up to the teacher').status_code == 200
    c = list(classroom); c[1] = substitute
    packet = request(c, method='get')
    assert packet.status_code == 200
    assert packet.data['packet']['substitute_instructions']
    assert not packet.data['can_delegate']
    assert 'teacher_notes_private' not in packet.data['packet']['lesson_plans'][0]
    assert request(c, operation='grant', account_id=str(classroom[1].id)).status_code == 403
    grant = ClassroomSubstituteGrant.objects.get(); grant.expires_at = now-timedelta(seconds=1); grant.save()
    assert request(c, method='get').status_code == 403


def test_only_school_authorized_substitute_account_may_receive_access(classroom):
    now = timezone.now()
    assert request(classroom, operation='grant', account_id=str(classroom[2].id), starts_at=now.isoformat(), expires_at=(now+timedelta(hours=2)).isoformat(), instructions='Packet').status_code == 400
    assert not ClassroomSubstituteGrant.objects.exists()


def test_emergency_starts_unknown_and_cannot_close_with_unaccounted_students(classroom):
    assert request(classroom, operation='emergency', kind='drill', title='Evacuation drill').status_code == 200
    session = ClassroomEmergencySession.objects.get()
    assert session.checks.get().state == 'unknown'
    assert request(classroom, operation='complete', session_id=str(session.id), version=1, note='Completed').status_code == 409
    assert request(classroom, operation='check', session_id=str(session.id), version=1, student_id=str(classroom[4].id), state='missing', note='Searching with school staff').status_code == 200
    assert request(classroom, operation='complete', session_id=str(session.id), version=2, note='Completed').status_code == 409
    assert request(classroom, operation='check', session_id=str(session.id), version=2, student_id=str(classroom[4].id), state='present', note='Confirmed at assembly point').status_code == 200
    assert request(classroom, operation='complete', session_id=str(session.id), version=3, note='All roster checks confirmed').status_code == 200
    session.refresh_from_db(); assert session.completed_at
    assert request(classroom, operation='check', session_id=str(session.id), version=4, student_id=str(classroom[4].id), state='missing', note='Rewrite').status_code == 409


def test_family_and_unrelated_staff_cannot_read_operational_roster(classroom):
    for user in [classroom[2], classroom[3], UserAccount.objects.create_user(username='staff-only', school=classroom[0], is_staff=True)]:
        c = list(classroom); c[1] = user
        assert request(c, method='get').status_code == 403


def test_unverified_roster_is_explicitly_unmarked(classroom):
    response = request(classroom, method='get')
    assert response.status_code == 200
    assert not response.data['roster'][0]['identity_verified']
    assert response.data['roster'][0]['attendance'] is None


def test_attendance_duplicate_rows_and_blank_reason_do_not_write(classroom):
    identity(classroom)
    row = {'student_id': str(classroom[4].id), 'status': 'PRESENT'}
    assert request(classroom, operation='attendance', version=0, items=[row, row], reason='Roll call').status_code == 400
    assert request(classroom, operation='attendance', version=0, items=[row], reason='').status_code == 400
    assert not AttendanceRecord.objects.exists()
