from datetime import timedelta
from decimal import Decimal
import pytest
from django.utils import timezone
from rest_framework.test import APIClient
from core.models import School, UserAccount, UserRole
from households.models import Guardian, Household, Student
from academics.models import Assignment, AssignmentCategory, Course, Enrollment, LessonPlan, Section, Submission
from gradebook.models import GradeEntry

pytestmark = pytest.mark.django_db
URL = '/api/v1/academics/classroom/workspace/'


@pytest.fixture
def classroom():
    school = School.objects.create(name='Classroom school')
    teacher = UserAccount.objects.create_user(username='classroom-teacher', email='teacher@example.com', school=school)
    UserRole.objects.create(user=teacher, school=school, role_code='TEACHER')
    parent = UserAccount.objects.create_user(username='classroom-parent', school=school, email='parent@example.com')
    student_account = UserAccount.objects.create_user(username='classroom-student', email='student@example.com', school=school)
    household = Household.objects.create(school_id=school.id, name='Classroom family')
    Guardian.objects.create(school_id=school.id, household=household, account=parent, first_name='Parent', last_name='One')
    student = Student.objects.create(school_id=school.id, household=household, account=student_account, first_name='Student', last_name='One')
    course = Course.objects.create(school_id=school.id, code='SCI', name='Science')
    section = Section.objects.create(school_id=school.id, course=course, term='2026-FALL', teacher=teacher)
    enrollment = Enrollment.objects.create(school_id=school.id, section=section, student=student)
    category = AssignmentCategory.objects.create(school_id=school.id, section=section, name='Practice')
    assignment = Assignment.objects.create(school_id=school.id, section=section, category=category,
                                            name='Observation', points_possible=10, due_date=timezone.localdate())
    LessonPlan.objects.create(school_id=school.id, section=section, plan_date=timezone.localdate(),
                               objectives='Observe creation', teacher_notes_private='Confidential teacher note')
    return school, teacher, parent, student_account, student, section, enrollment, category, assignment


def get(user, school, **params):
    client = APIClient()
    client.force_authenticate(user)
    return client.get(URL, params, HTTP_X_SCHOOL_ID=str(school.id))


@pytest.mark.parametrize('position,audience', [(1, 'teacher'), (2, 'parent'), (3, 'student')])
def test_workspace_uses_verified_relationships_and_hides_private_notes(classroom, position, audience):
    school, *rest = classroom
    response = get(classroom[position], school, audience=audience)
    assert response.status_code == 200
    assert len(response.data['assignments']) == 1
    assert response.data['lesson_plans'][0]['objectives'] == 'Observe creation'
    assert 'teacher_notes_private' not in response.data['lesson_plans'][0]
    assert response.data['source'] == 'live'


def test_matching_email_and_staff_flag_do_not_grant_classroom_access(classroom):
    school = classroom[0]
    stranger = UserAccount.objects.create_user(username='stranger', school=school, email='stranger@example.com', is_staff=True)
    Guardian.objects.filter(account=classroom[2]).update(email=stranger.email)
    for audience in ('parent', 'student', 'admin', 'teacher', 'board'):
        assert get(stranger, school, audience=audience).status_code == 403


def test_families_never_see_unpublished_assignments(classroom):
    school, teacher, parent, _, _, section, _, category, _ = classroom
    Assignment.objects.create(school_id=school.id, section=section, category=category, name='Draft', points_possible=5, is_published=False)
    assert len(get(parent, school, audience='parent').data['assignments']) == 1
    assert len(get(teacher, school, audience='teacher').data['assignments']) == 2


def test_submission_receipt_is_not_missing_or_a_zero_grade(classroom):
    school, _, parent, _, student, section, enrollment, _, assignment = classroom
    Submission.objects.create(school_id=school.id, enrollment=enrollment, assignment=assignment,
                               submitted_at=timezone.now(), status='submitted')
    task = get(parent, school, audience='parent').data['assignments'][0]
    assert task['state'] == 'awaiting_grading'
    assert task['points_earned'] is None
    GradeEntry.objects.create(school_id=school.id, section=section, student=student, assignment=assignment,
                               assignment_name=assignment.name, points_earned=Decimal('0'), points_possible=10)
    task = get(parent, school, audience='parent').data['assignments'][0]
    assert task['state'] == 'graded'
    assert task['points_earned'] == 0


def test_overdue_without_evidence_is_not_marked_missing(classroom):
    school, _, parent, *_, assignment = classroom
    assignment.due_date = timezone.localdate() - timedelta(days=1)
    assignment.save()
    date = assignment.due_date.isoformat()
    task = get(parent, school, audience='parent', **{'from': date}).data['assignments'][0]
    assert task['state'] == 'overdue_unconfirmed'


def test_board_returns_aggregate_evidence_without_individual_records(classroom):
    school = classroom[0]
    board = UserAccount.objects.create_user(username='board', email='board@example.com', school=school)
    UserRole.objects.create(user=board, school=school, role_code='BOARD_MEMBER')
    result = get(board, school, audience='board').data
    assert result['summary']['section_enrollments'] == 1
    for key in ('students', 'assignments', 'lesson_plans', 'categories', 'sections'):
        assert key not in result


@pytest.mark.parametrize('params', [{'audience': 'unknown'}, {'section_id': 'bad'}, {'student_id': 'bad'},
                                   {'from': '2026-99-99'}, {'from': 'bad'}, {'from': '2026-01-01', 'to': '2026-12-01'}])
def test_invalid_filters_fail_cleanly(classroom, params):
    assert get(classroom[1], classroom[0], **params).status_code == 400


def test_teacher_has_no_other_section_roster(classroom):
    school, teacher, _, _, student, _, _, _, _ = classroom
    other = Section.objects.create(school_id=school.id, course=Course.objects.create(school_id=school.id, code='OTHER', name='Other'), term='2026')
    Enrollment.objects.create(school_id=school.id, section=other, student=student)
    result = get(teacher, school, audience='teacher', section_id=str(other.id)).data
    assert result['sections'] == []
    assert result['assignments'] == []


def test_cross_school_and_inactive_household_fail_closed(classroom):
    school, _, parent, _, student, *_ = classroom
    other = School.objects.create(name='Other school')
    assert get(parent, other, audience='parent').status_code == 404
    student.household.is_active = False
    student.household.save()
    assert get(parent, school, audience='parent').status_code == 403


def test_existing_lesson_endpoint_never_releases_private_notes_to_other_roles(classroom):
    school, teacher, parent, *_ = classroom
    UserRole.objects.create(user=parent, school=school, role_code='PARENT')
    unassigned = UserAccount.objects.create_user(username='other-teacher', email='other-teacher@example.com', school=school)
    UserRole.objects.create(user=unassigned, school=school, role_code='TEACHER')
    plan = LessonPlan.objects.get(school_id=school.id)
    client = APIClient()
    for user in (parent, unassigned):
        client.force_authenticate(user)
        response = client.get(f'/api/v1/academics/lesson-plans/{plan.id}/', HTTP_X_SCHOOL_ID=str(school.id))
        assert response.status_code == 200
        assert 'teacher_notes_private' not in response.data
    client.force_authenticate(teacher)
    assert 'teacher_notes_private' in client.get(f'/api/v1/academics/lesson-plans/{plan.id}/', HTTP_X_SCHOOL_ID=str(school.id)).data
