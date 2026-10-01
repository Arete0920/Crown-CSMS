import json
import uuid
from datetime import timedelta
import pytest
from django.utils import timezone
from rest_framework.test import APIClient
from core.models import UserAccount, UserRole
from academics.tests.test_classroom_experience import classroom
from academics.models import Submission, TeacherAssignment
from academics.collaboration_models import ClassroomRecord
from academics.support_models import ClassroomInterventionLink
from signals.models import InterventionCase

pytestmark = pytest.mark.django_db
URL = '/api/v1/academics/classroom/leadership/'


def reader(c, role='ADMIN'):
    account = UserAccount.objects.create_user(username='leader-'+role, email=role.lower()+'@leaders.example.com', school=c[0])
    UserRole.objects.create(user=account, school=c[0], role_code=role)
    client = APIClient(); client.force_authenticate(account)
    return client


def report(c, client, **params):
    return client.get(URL, {'audience': 'admin', **params}, HTTP_X_SCHOOL_ID=str(c[0].id))


def test_board_has_aggregate_sources_without_names_or_staff_rows(classroom):
    classroom[4].first_name = 'SensitiveLearnerName'
    classroom[4].save()
    r = report(classroom, reader(classroom, 'BOARD'), audience='board')
    assert r.status_code == 200
    assert 'sections' not in r.data and 'teacher_workload' not in r.data
    serialized = json.dumps(r.data, default=str)
    for value in [str(classroom[4].id), classroom[1].username, classroom[4].first_name, 'Confidential teacher note']:
        assert value not in serialized
    assert r.data['summary']['section_enrollments'] == 1
    assert r.data['provenance'] and r.data['summary']['definitions']


def test_parent_student_teacher_and_staff_flag_cannot_read_leadership(classroom):
    client = APIClient()
    for account in classroom[1:4]:
        client.force_authenticate(account)
        assert report(classroom, client).status_code == 403
    stranger = UserAccount.objects.create_user(username='staff-flag', school=classroom[0], is_staff=True)
    client.force_authenticate(stranger)
    assert report(classroom, client).status_code == 403


def test_workload_deduplicates_primary_and_staff_assignment(classroom):
    TeacherAssignment.objects.create(school_id=classroom[0].id, section=classroom[5], staff=classroom[1].staff)
    Submission.objects.create(school_id=classroom[0].id, assignment=classroom[8], enrollment=classroom[6], submitted_at=timezone.now(), status='submitted')
    r = report(classroom, reader(classroom))
    assert r.status_code == 200
    workload = r.data['teacher_workload'][0]
    assert workload['sections'] == workload['section_enrollments'] == workload['unique_students'] == 1
    assert workload['pending_grading'] == 1
    assert workload['planned_minutes'] is None
    assert r.data['summary']['recorded_actual_minutes'] is None


def test_current_support_inventory_is_separate_from_dated_activity(classroom):
    linked = InterventionCase.objects.create(school_id=classroom[0].id, student=classroom[4], reason='Private reason', review_at=timezone.now()-timedelta(days=1))
    ClassroomInterventionLink.objects.create(school_id=classroom[0].id, section=classroom[5], case=linked)
    InterventionCase.objects.create(school_id=classroom[0].id, student=classroom[4], reason='Legacy unlinked')
    past = timezone.localdate()-timedelta(days=20)
    r = report(classroom, reader(classroom, 'BOARD'), audience='board', **{'from':past.isoformat(), 'to':past.isoformat()})
    summary = r.data['summary']
    assert summary['published_assignments_due'] == 0
    assert summary['open_linked_support_cases'] == summary['overdue_linked_support_reviews'] == summary['unlinked_school_support_cases'] == 1
    assert summary['linked_cases_without_verified_owner'] == 1
    assert 'Private reason' not in json.dumps(r.data, default=str)


def test_zero_resource_cost_is_preserved_and_invalid_window_rejected(classroom):
    ClassroomRecord.objects.create(school_id=classroom[0].id, section=classroom[5], kind='resource', title='Reusable book', body='School resource', visibility='class', owner=classroom[1], created_by=classroom[1], request_key=uuid.uuid4(), fingerprint='resource', metadata={'cost_cents':0})
    client = reader(classroom)
    assert report(classroom, client).data['summary']['recorded_resource_cost_cents'] == 0
    assert report(classroom, client, **{'from':'2026-01-01', 'to':'2026-03-01'}).status_code == 400
    assert report(classroom, client, section_id=str(classroom[5].id)).status_code == 400
    assert client.post(URL, {}, format='json', HTTP_X_SCHOOL_ID=str(classroom[0].id)).status_code == 405


def test_planning_target_uses_current_roster_and_never_changes_sections(classroom):
    from academics.models import Enrollment, Section
    from households.models import Student
    c = classroom
    for name in ['Second', 'Third']:
        student = Student.objects.create(school_id=c[0].id, household=c[4].household, first_name=name, last_name='Student')
        Enrollment.objects.create(school_id=c[0].id, section=c[5], student=student)
    client = reader(c)
    before = Section.objects.count()
    response = report(c, client, target_class_size='2')
    assert response.status_code == 200
    assert response.data['summary']['sections_above_target'] == 1
    assert response.data['summary']['additional_sections_for_target'] == 1
    assert response.data['sections'][0]['verified_teachers'] == 1
    assert Section.objects.count() == before
    assert report(c, client).data['summary']['sections_above_target'] is None
    for invalid in ['0', '-1', '2.5', '1001', 'false']:
        assert report(c, client, target_class_size=invalid).status_code == 400


def test_staffing_counts_require_active_verified_teacher_relationship(classroom):
    c = classroom
    client = reader(c, 'BOARD')
    c[1].staff.status = 'INACTIVE'
    c[1].staff.save()
    response = report(c, client, audience='board', target_class_size='20')
    assert response.data['summary']['sections_without_verified_teacher'] == 1
    assert 'sections' not in response.data and 'teacher_workload' not in response.data
    assert str(c[1].id) not in json.dumps(response.data, default=str)


def test_curriculum_coverage_deduplicates_delivery_and_exposes_alignment(classroom):
    from academics.tests.test_classroom_instruction import curriculum
    from academics.models import Lesson, LessonPlan, PublisherObjective
    from academics.lesson_execution_models import LessonPlanLesson
    c = classroom
    lesson, objective, plan = curriculum(c)
    other = Lesson.objects.create(school_id=c[0].id, unit=lesson.unit, title='Next lesson')
    PublisherObjective.objects.create(school_id=c[0].id, lesson=other, objective_code='SCI-2', description='Next objective')
    link = LessonPlanLesson.objects.get(lesson_plan=plan, lesson=lesson)
    link.delivery_status = 'taught'; link.actual_completed_at = timezone.now(); link.actual_minutes = 25; link.save()
    duplicate = LessonPlan.objects.create(school_id=c[0].id, section=c[5], plan_date=timezone.localdate()-timedelta(days=1), lesson_ids=[str(lesson.id)])
    duplicate_link = duplicate.lesson_links.get()
    duplicate_link.delivery_status = 'taught'; duplicate_link.actual_completed_at = timezone.now(); duplicate_link.save()
    c[8].objective = objective; c[8].lesson = other; c[8].save()
    client = reader(c)
    result = report(c, client, **{'from': duplicate.plan_date.isoformat(), 'to': plan.plan_date.isoformat()})
    row = result.data['curriculum_coverage'][0]
    assert row['known_objectives'] == 2
    assert row['planned_objectives'] == row['confirmed_taught_objectives'] == row['unplanned_objectives'] == 1
    assert row['known_objective_delivery_percent'] == 50
    assert row['alignment_issues'] == 1
    assert result.data['summary']['recorded_instructional_time_percent'] is None
    board = report(c, reader(c, 'BOARD'), audience='board')
    assert 'curriculum_coverage' not in board.data
    assert 'Next objective' not in json.dumps(board.data, default=str)


def test_attendance_denominator_is_frozen_complete_and_not_current_roster(classroom):
    from academics.tests.test_classroom_operations import identity, request
    from academics.models import Enrollment
    from academics.operations_models import ClassroomAttendanceSession
    from crown_api.models import AttendanceRecord
    from households.models import Student
    c = classroom
    core = identity(c)
    assert request(c, operation='attendance', version=0, items=[{'student_id': str(c[4].id), 'status': 'PRESENT'}], reason='Verified roll call').status_code == 200
    new_student = Student.objects.create(school_id=c[0].id, household=c[4].household, first_name='Later', last_name='Enrollment')
    Enrollment.objects.create(school_id=c[0].id, section=c[5], student=new_student)
    summary = report(c, reader(c)).data['summary']
    assert summary['known_expected_student_sessions'] == summary['recorded_expected_statuses'] == 1
    assert summary['audited_session_presence_percent'] == 100
    session = ClassroomAttendanceSession.objects.get()
    from django.core.exceptions import ValidationError
    session.expected_roster = []
    with pytest.raises(ValidationError): session.save()
    with pytest.raises(ValidationError): ClassroomAttendanceSession.objects.filter(pk=session.pk).update(expected_roster=[])
    AttendanceRecord.objects.filter(student=core).delete()
    summary = report(c, reader(c, 'BOARD'), audience='board').data['summary']
    assert summary['unrecorded_expected_statuses'] == 1
    assert summary['audited_session_presence_percent'] is None


def test_legacy_and_unverified_rosters_withhold_attendance_rate(classroom):
    from academics.operations_models import ClassroomAttendanceSession
    c = classroom
    ClassroomAttendanceSession.objects.create(school_id=c[0].id, section=c[5], date=timezone.localdate(),
        expected_roster=[{'student_id': str(c[4].id), 'core_student_id': None}])
    ClassroomAttendanceSession.objects.create(school_id=c[0].id, section=c[5], date=timezone.localdate()-timedelta(days=1))
    summary = report(c, reader(c), **{'from': (timezone.localdate()-timedelta(days=1)).isoformat()}).data['summary']
    assert summary['sessions_without_expected_roster'] == summary['unverified_expected_identities'] == 1
    assert summary['audited_session_presence_percent'] is None


def test_recorded_time_ratio_keeps_zero_and_requires_every_denominator(classroom):
    from academics.tests.test_classroom_instruction import curriculum
    from academics.lesson_execution_models import LessonPlanLesson
    lesson, _, plan = curriculum(classroom)
    link = LessonPlanLesson.objects.get(lesson=lesson, lesson_plan=plan)
    link.actual_minutes = 0; link.save()
    result = report(classroom, reader(classroom)).data['summary']
    assert result['recorded_instructional_time_percent'] == 0
    assert result['lesson_links_missing_time_evidence'] == 0
