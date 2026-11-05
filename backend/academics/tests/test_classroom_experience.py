from datetime import timedelta
from decimal import Decimal
import pytest
from django.utils import timezone
from rest_framework.test import APIClient
from core.models import CrownPermission, RolePermission, School, Staff, UserAccount, UserRole
from core.permissions import user_has_permission
from households.models import Guardian, Household, Student
from academics.models import Assignment, AssignmentCategory, Course, Enrollment, LessonPlan, Section, Submission
from gradebook.models import GradeEntry
from signals.models import BoardExecutiveMetric

pytestmark = pytest.mark.django_db
URL = '/api/v1/academics/classroom/workspace/'
BOARD_READ_URLS = (
    (URL, {"audience": "board"}),
    ("/api/v1/academics/classroom/leadership/", {"audience": "board"}),
    ("/api/signals/board/risk-counts/", {}),
    ("/api/signals/board/compass/", {}),
)


@pytest.fixture
def classroom():
    # Baseline fixtures use timezone.localdate() (Django TIME_ZONE=UTC).
    # Set the fixture school to UTC; explicit school-timezone tests override it.
    school = School.objects.create(name='Classroom school', timezone='UTC')
    teacher = UserAccount.objects.create_user(username='classroom-teacher', email='teacher@example.com', school=school)
    teacher.staff = Staff.objects.create(school=school, first_name='Teacher', last_name='One', email=teacher.email, role_type='TEACHER', status='ACTIVE')
    teacher.save(update_fields=['staff'])
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


def _grant_board_read(role_code):
    permission, _ = CrownPermission.objects.get_or_create(code="board.view")
    grant, _ = RolePermission.objects.get_or_create(role_code=role_code, permission=permission)
    return grant


def _board_reads(user, school):
    client = APIClient()
    client.force_authenticate(user)
    return [
        client.get(url, params, HTTP_X_SCHOOL_ID=str(school.id))
        for url, params in BOARD_READ_URLS
    ]


@pytest.fixture
def board_school(classroom):
    school = classroom[0]
    BoardExecutiveMetric.objects.create(
        school=school, as_of_date=timezone.localdate(),
        highlights=["Authorized school aggregate"],
    )
    return school


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
    _grant_board_read("BOARD_MEMBER")
    result = get(board, school, audience='board').data
    assert result['summary']['section_enrollments'] == 1
    for key in ('students', 'assignments', 'lesson_plans', 'categories', 'sections'):
        assert key not in result



def test_canonical_board_member_can_read_board_summaries_but_not_admin_or_other_tenants(classroom):
    school = classroom[0]
    board = UserAccount.objects.create_user(
        username="least-privilege-board", email="least-board@example.invalid", school=school,
    )
    UserRole.objects.create(user=board, school=school, role_code="board_member")
    _grant_board_read("board_member")

    classroom_board = get(board, school, audience="board")
    assert classroom_board.status_code == 200
    assert "students" not in classroom_board.data
    assert get(board, school, audience="admin").status_code == 403

    client = APIClient()
    client.force_authenticate(user=board)
    board_counts = client.get(
        "/api/signals/board/risk-counts/", HTTP_X_SCHOOL_ID=str(school.id),
    )
    assert board_counts.status_code == 200, board_counts.content
    other_school = School.objects.create(name="Unrelated Board Tenant")
    denied = client.get(
        "/api/signals/board/risk-counts/", HTTP_X_SCHOOL_ID=str(other_school.id),
    )
    assert denied.status_code in (403, 404)
    assert get(board, other_school, audience="board").status_code == 404


def test_heritage_board_session_provisions_canonical_permission_and_obeys_revocation(settings):
    from sandbox_demo.catalog import SANDBOX_PERSONAS

    settings.CROWN_SANDBOX_ALLOW_OPEN_SESSION = True
    RolePermission.objects.filter(role_code="board_member", permission__code="board.view").delete()
    session_response = APIClient().post(
        "/api/v1/sandbox/session/",
        {"role": "board", "school": "heritage-core", "track": "school"},
        format="json",
    )
    assert session_response.status_code == 201
    school = School.objects.get(pk=session_response.data["school_id"])
    board = UserAccount.objects.get(username=SANDBOX_PERSONAS["board"].email, school=school)
    assert set(board.roles.values_list("role_code", flat=True)) == {"board_member"}
    assert user_has_permission(board, "board.view", school=school)
    assert not user_has_permission(board, "admin.view", school=school)
    BoardExecutiveMetric.objects.create(school=school, as_of_date=timezone.localdate())

    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {session_response.data['access']}")
    for url, params in BOARD_READ_URLS:
        response = client.get(url, params, HTTP_X_SCHOOL_ID=str(school.id))
        assert response.status_code == 200, response.content

    RolePermission.objects.filter(role_code="board_member", permission__code="board.view").delete()
    for url, params in BOARD_READ_URLS:
        response = client.get(url, params, HTTP_X_SCHOOL_ID=str(school.id))
        assert response.status_code == 403, response.content


def _issue_heritage_board_session(settings):
    settings.TENANT_HEADER_REQUIRED = True
    settings.CROWN_SANDBOX_ALLOW_OPEN_SESSION = True
    response = APIClient().post(
        "/api/v1/sandbox/session/",
        {"role": "board", "school": "heritage-core", "track": "school"},
        format="json",
    )
    assert response.status_code == 201
    assert response.data["role_code"] == "board_member"
    return response.data


def test_heritage_board_bearer_renewal_preserves_foreign_tenant_denials(settings):
    from sandbox_demo.catalog import SANDBOX_PERSONAS

    first = _issue_heritage_board_session(settings)
    school = School.objects.get(pk=first["school_id"])
    board = UserAccount.objects.get(username=SANDBOX_PERSONAS["board"].email, school=school)
    foreign_schools = [School.objects.create(name=f"Unrelated Board Tenant {index}") for index in range(2)]
    board_routes = (
        "/api/signals/board/risk-counts/",
        "/api/v1/nav/",
        "/api/v1/academics/classroom/workspace/?audience=board",
    )

    def verify_session(session):
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {session['access']}")
        for route in board_routes:
            own = client.get(route, HTTP_X_SCHOOL_ID=str(school.id))
            assert own.status_code == 200, own.content
        for route in (
            "/api/v1/academics/classroom/workspace/?audience=admin",
            "/api/v1/admin/metrics/",
            "/api/v1/finance/metrics/",
            "/api/v1/sandbox/admin/state/",
            "/api/v1/sandbox/finance/state/",
        ):
            denied = client.get(route, HTTP_X_SCHOOL_ID=str(school.id))
            assert denied.status_code == 403, denied.content
        for foreign in foreign_schools:
            for route in board_routes:
                denied = client.get(route, HTTP_X_SCHOOL_ID=str(foreign.id))
                assert denied.status_code == 404, denied.content
                assert denied.json()["code"] == "tenant_access_denied"

    verify_session(first)
    assert board.staff_id is None
    stale_staff, _ = Staff.objects.update_or_create(
        school=school, email=board.email,
        defaults={"first_name": "Historical", "last_name": "Board", "role_type": "SUPPORT", "status": "ACTIVE"},
    )
    board.staff = stale_staff
    board.save(update_fields=["staff"])
    UserRole.objects.create(school=school, user=board, role_code="HEAD_OF_SCHOOL")

    second = _issue_heritage_board_session(settings)
    assert second["school_id"] == first["school_id"]
    board.refresh_from_db()
    assert board.staff_id is None
    assert set(board.roles.values_list("role_code", flat=True)) == {"board_member"}
    assert Staff.objects.filter(pk=stale_staff.pk).exists()
    for session in (first, second):
        for _read in range(2):
            verify_session(session)


def test_board_and_support_tenant_override_do_not_grant_private_household_access(settings):
    from crown_api.jwt_utils import build_access_token

    session = _issue_heritage_board_session(settings)
    school = School.objects.get(pk=session["school_id"])
    foreign = School.objects.create(name="Foreign household tenant")
    household = Household.objects.create(school_id=foreign.id, name="Synthetic foreign household")
    route = f"/api/v1/households/{household.id}/"
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {session['access']}")
    denied = client.get(route, HTTP_X_SCHOOL_ID=str(foreign.id))
    assert denied.status_code == 404, denied.content
    assert denied.json()["code"] == "tenant_access_denied"

    staff = Staff.objects.create(
        school=school, email="authorized-support@example.invalid", first_name="Authorized",
        last_name="Support", role_type="SUPPORT", status="ACTIVE",
    )
    support = UserAccount.objects.create_user(
        username="authorized-support", email=staff.email, school=school, staff=staff,
    )
    token = build_access_token(
        user_id=str(support.id), email=support.email, role="SUPPORT", school_id=str(school.id),
    )
    _issue_heritage_board_session(settings)
    support.refresh_from_db()
    assert support.staff_id == staff.id
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    # Cross-tenant selection does not itself confer protected household
    # directory privileges, even to genuine staff with SUPPORT duties.
    denied_support = client.get(route, HTTP_X_SCHOOL_ID=str(foreign.id))
    assert denied_support.status_code == 404, denied_support.content
    assert str(household.id) not in str(denied_support.content)
    assert household.name not in str(denied_support.content)


@pytest.mark.parametrize("persona_key,staff_role", [("teacher", "TEACHER"), ("school_admin", "ADMIN")])
def test_board_renewal_preserves_other_staff_personas(settings, persona_key, staff_role):
    from sandbox_demo.catalog import SANDBOX_PERSONAS
    from sandbox_demo.services import ensure_persona_user

    session = _issue_heritage_board_session(settings)
    school = School.objects.get(pk=session["school_id"])
    other = ensure_persona_user(school, SANDBOX_PERSONAS[persona_key])
    staff_id = other.staff_id
    assert staff_id is not None
    assert other.staff.role_type == staff_role
    _issue_heritage_board_session(settings)
    other.refresh_from_db()
    assert other.staff_id == staff_id
    assert other.staff.role_type == staff_role


@pytest.mark.parametrize("role_code", ["board_member", "BOARD_MEMBER", "BOARD", "board", "school_board"])
def test_board_reads_require_current_permission_and_reject_revocation(board_school, role_code):
    board = UserAccount.objects.create_user(
        username="permission-board", email="permission-board@example.invalid", school=board_school,
    )
    UserRole.objects.create(user=board, school=board_school, role_code=role_code)
    RolePermission.objects.filter(role_code=role_code, permission__code="board.view").delete()

    for response in _board_reads(board, board_school):
        assert response.status_code == 403, response.content

    grant = _grant_board_read(role_code)
    responses = _board_reads(board, board_school)
    for response in responses:
        assert response.status_code == 200, response.content
    assert responses[0].data["summary"]["section_enrollments"] == 1
    assert "students" not in responses[0].data
    assert responses[3].data["highlights"] == ["Authorized school aggregate"]

    grant.delete()
    assert UserRole.objects.filter(user=board, school=board_school, role_code=role_code).exists()
    for response in _board_reads(board, board_school):
        assert response.status_code == 403, response.content


def test_board_permission_from_another_school_does_not_authorize_reads(board_school):
    board = UserAccount.objects.create_user(
        username="cross-school-board", email="cross-school-board@example.invalid", school=board_school,
    )
    UserRole.objects.create(user=board, school=board_school, role_code="board_member")
    RolePermission.objects.filter(role_code="board_member", permission__code="board.view").delete()
    other_school = School.objects.create(name="Permission grant in another school")
    UserRole.objects.create(user=board, school=other_school, role_code="BOARD_MEMBER")
    _grant_board_read("BOARD_MEMBER")
    assert user_has_permission(board, "board.view", school=other_school)
    assert not user_has_permission(board, "board.view", school=board_school)

    for response in _board_reads(board, board_school):
        assert response.status_code == 403, response.content


def test_board_permission_without_board_or_leadership_role_does_not_authorize_reads(board_school):
    teacher = UserAccount.objects.create_user(
        username="permission-teacher", email="permission-teacher@example.invalid", school=board_school,
    )
    UserRole.objects.create(user=teacher, school=board_school, role_code="TEACHER")
    _grant_board_read("TEACHER")
    assert user_has_permission(teacher, "board.view", school=board_school)

    for response in _board_reads(teacher, board_school):
        assert response.status_code == 403, response.content


@pytest.mark.parametrize("superuser", [False, True])
def test_existing_leadership_board_reads_remain_available_without_board_grant(board_school, superuser):
    leader = UserAccount.objects.create_user(
        username="existing-leader", email="existing-leader@example.invalid", school=board_school,
        is_superuser=superuser,
    )
    if not superuser:
        UserRole.objects.create(user=leader, school=board_school, role_code="HEAD_OF_SCHOOL")
        RolePermission.objects.filter(role_code="HEAD_OF_SCHOOL", permission__code="board.view").delete()
    assert not user_has_permission(leader, "board.view", school=board_school)

    for response in _board_reads(leader, board_school):
        assert response.status_code == 200, response.content


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
