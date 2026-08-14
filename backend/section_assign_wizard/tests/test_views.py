import uuid
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from academics.models import Course, Enrollment, Section
from core.models import CrownPermission, RolePermission, School, UserRole
from households.models import Household, Student
from section_assign_wizard.models import SectionAssignWizardSession


TEST_AUTH_SECRET = "TestAuthSecret-LocalOnly"

User = get_user_model()

BASE_URL = "/api/v1/section-assign-wizard/sessions/"


def _make_school(name=None):
    name = name or f"School {uuid.uuid4().hex[:6]}"
    return School.objects.create(name=name, timezone="America/Chicago", is_active=True)


def _make_user(school=None, username=None):
    username = username or f"user_{uuid.uuid4().hex[:8]}"
    return User.objects.create_user(username=username, password=TEST_AUTH_SECRET)


def _make_section(school_id, term="2026-FALL"):
    course = Course.objects.create(
        school_id=school_id, code=f"CS{uuid.uuid4().hex[:4]}", name="Test Course"
    )
    return Section.objects.create(
        school_id=school_id, course=course, term=term
    )


def _make_student(school_id):
    """Create a Household + Student for FK-safe tests."""
    household = Household.objects.create(school_id=school_id, name=f"HH {uuid.uuid4().hex[:6]}")
    return Student.objects.create(
        school_id=school_id,
        household=household,
        first_name="Test",
        last_name=f"Student{uuid.uuid4().hex[:4]}",
    )


def _headers(school_id):
    return {"HTTP_X_SCHOOL_ID": str(school_id)}


def _grant_wizard_access(user, school):
    UserRole.objects.get_or_create(user=user, school=school, role_code="REGISTRAR")
    for code in ("rosters.edit", "academics.view"):
        permission, _ = CrownPermission.objects.get_or_create(
            code=code,
            defaults={"description": f"test permission {code}"},
        )
        RolePermission.objects.get_or_create(role_code="REGISTRAR", permission=permission)


def _client_for(school):
    user = _make_user(school)
    _grant_wizard_access(user, school)
    c = APIClient()
    c.force_authenticate(user=user)
    return c


# ---------------------------------------------------------------------------
# Advance helpers
# ---------------------------------------------------------------------------

def _advance_to_configured(client, school_id, section_id, term="2026-FALL"):
    r = client.post(BASE_URL, **_headers(school_id))
    session_id = r.data["session_id"]
    client.post(
        f"{BASE_URL}{session_id}/configure/",
        {"section_id": str(section_id), "term": term},
        format="json",
        **_headers(school_id),
    )
    return session_id


def _advance_to_students_loaded(client, school_id, section_id, student_ids=None):
    session_id = _advance_to_configured(client, school_id, section_id)
    if student_ids is None:
        student_ids = [str(uuid.uuid4()) for _ in range(3)]
    client.post(
        f"{BASE_URL}{session_id}/load/",
        {"student_ids": student_ids},
        format="json",
        **_headers(school_id),
    )
    return session_id, student_ids


def _advance_to_roster_staged(client, school_id, section_id, student_ids=None):
    session_id, student_ids = _advance_to_students_loaded(client, school_id, section_id, student_ids)
    changes = [{"student_id": sid, "action": "add"} for sid in student_ids[:2]]
    client.post(
        f"{BASE_URL}{session_id}/stage/",
        {"changes": changes},
        format="json",
        **_headers(school_id),
    )
    return session_id, student_ids


# ---------------------------------------------------------------------------
# TestAuth
# ---------------------------------------------------------------------------

class TestAuth(TestCase):
    def setUp(self):
        self.school = _make_school()

    def test_create_requires_auth(self):
        c = APIClient()
        r = c.post(BASE_URL, **_headers(self.school.id))
        self.assertEqual(r.status_code, 401)

    def test_configure_requires_auth(self):
        c = APIClient()
        r = c.post(f"{BASE_URL}{uuid.uuid4()}/configure/", **_headers(self.school.id))
        self.assertEqual(r.status_code, 401)


# ---------------------------------------------------------------------------
# TestTenantIsolation
# ---------------------------------------------------------------------------

class TestTenantIsolation(TestCase):
    def setUp(self):
        self.school_a = _make_school("School A")
        self.school_b = _make_school("School B")
        self.client_a = _client_for(self.school_a)
        self.client_b = _client_for(self.school_b)
        self.section_a = _make_section(self.school_a.id)

        r = self.client_a.post(BASE_URL, **_headers(self.school_a.id))
        self.session_id = r.data["session_id"]

    def test_configure_wrong_school(self):
        r = self.client_b.post(
            f"{BASE_URL}{self.session_id}/configure/",
            {"section_id": str(self.section_a.id), "term": "2026-FALL"},
            format="json",
            **_headers(self.school_b.id),
        )
        self.assertEqual(r.status_code, 404)

    def test_load_wrong_school(self):
        r = self.client_b.post(
            f"{BASE_URL}{self.session_id}/load/",
            {"student_ids": [str(uuid.uuid4())]},
            format="json",
            **_headers(self.school_b.id),
        )
        self.assertEqual(r.status_code, 404)

    def test_stage_wrong_school(self):
        r = self.client_b.post(
            f"{BASE_URL}{self.session_id}/stage/",
            {"changes": [{"student_id": str(uuid.uuid4()), "action": "add"}]},
            format="json",
            **_headers(self.school_b.id),
        )
        self.assertEqual(r.status_code, 404)

    def test_commit_wrong_school(self):
        r = self.client_b.post(
            f"{BASE_URL}{self.session_id}/commit/",
            {"confirm": True},
            format="json",
            **_headers(self.school_b.id),
        )
        self.assertEqual(r.status_code, 404)

    def test_verify_wrong_school(self):
        r = self.client_b.get(
            f"{BASE_URL}{self.session_id}/verify/",
            **_headers(self.school_b.id),
        )
        self.assertEqual(r.status_code, 404)


# ---------------------------------------------------------------------------
# TestCreateSession
# ---------------------------------------------------------------------------

class TestCreateSession(TestCase):
    def setUp(self):
        self.school = _make_school()
        self.client = _client_for(self.school)

    def test_create_returns_201_session_id(self):
        r = self.client.post(BASE_URL, **_headers(self.school.id))
        self.assertEqual(r.status_code, 201)
        self.assertIn("session_id", r.data)

    def test_two_sessions_distinct(self):
        r1 = self.client.post(BASE_URL, **_headers(self.school.id))
        r2 = self.client.post(BASE_URL, **_headers(self.school.id))
        self.assertNotEqual(r1.data["session_id"], r2.data["session_id"])


# ---------------------------------------------------------------------------
# TestConfigure
# ---------------------------------------------------------------------------

class TestConfigure(TestCase):
    def setUp(self):
        self.school = _make_school()
        self.client = _client_for(self.school)
        self.section = _make_section(self.school.id)
        r = self.client.post(BASE_URL, **_headers(self.school.id))
        self.session_id = r.data["session_id"]

    def test_configure_success(self):
        r = self.client.post(
            f"{BASE_URL}{self.session_id}/configure/",
            {"section_id": str(self.section.id), "term": "2026-FALL"},
            format="json",
            **_headers(self.school.id),
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["status"], "configured")
        self.assertEqual(r.data["term"], "2026-FALL")

    def test_configure_missing_section_id(self):
        r = self.client.post(
            f"{BASE_URL}{self.session_id}/configure/",
            {"term": "2026-FALL"},
            format="json",
            **_headers(self.school.id),
        )
        self.assertEqual(r.status_code, 400)

    def test_configure_invalid_section_uuid(self):
        r = self.client.post(
            f"{BASE_URL}{self.session_id}/configure/",
            {"section_id": "not-a-uuid", "term": "2026-FALL"},
            format="json",
            **_headers(self.school.id),
        )
        self.assertEqual(r.status_code, 400)

    def test_configure_wrong_school_section(self):
        other_school = _make_school("Other")
        other_section = _make_section(other_school.id)
        r = self.client.post(
            f"{BASE_URL}{self.session_id}/configure/",
            {"section_id": str(other_section.id), "term": "2026-FALL"},
            format="json",
            **_headers(self.school.id),
        )
        self.assertEqual(r.status_code, 404)


# ---------------------------------------------------------------------------
# TestLoadStudents
# ---------------------------------------------------------------------------

class TestLoadStudents(TestCase):
    def setUp(self):
        self.school = _make_school()
        self.client = _client_for(self.school)
        self.section = _make_section(self.school.id)
        self.session_id = _advance_to_configured(
            self.client, self.school.id, self.section.id
        )

    def test_load_success(self):
        ids = [str(uuid.uuid4()) for _ in range(4)]
        r = self.client.post(
            f"{BASE_URL}{self.session_id}/load/",
            {"student_ids": ids},
            format="json",
            **_headers(self.school.id),
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["status"], "students_loaded")
        self.assertEqual(r.data["student_count"], 4)

    def test_load_empty_rejected(self):
        r = self.client.post(
            f"{BASE_URL}{self.session_id}/load/",
            {"student_ids": []},
            format="json",
            **_headers(self.school.id),
        )
        self.assertEqual(r.status_code, 400)

    def test_load_invalid_uuid_rejected(self):
        r = self.client.post(
            f"{BASE_URL}{self.session_id}/load/",
            {"student_ids": ["not-a-uuid"]},
            format="json",
            **_headers(self.school.id),
        )
        self.assertEqual(r.status_code, 400)

    def test_load_deduplicates(self):
        sid = str(uuid.uuid4())
        r = self.client.post(
            f"{BASE_URL}{self.session_id}/load/",
            {"student_ids": [sid, sid, sid]},
            format="json",
            **_headers(self.school.id),
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["student_count"], 1)

    def test_load_wrong_state(self):
        # Load twice → second is wrong state (already students_loaded after first)
        ids = [str(uuid.uuid4())]
        self.client.post(
            f"{BASE_URL}{self.session_id}/load/",
            {"student_ids": ids},
            format="json",
            **_headers(self.school.id),
        )
        # Now status = students_loaded; load again should fail
        r = self.client.post(
            f"{BASE_URL}{self.session_id}/load/",
            {"student_ids": ids},
            format="json",
            **_headers(self.school.id),
        )
        self.assertEqual(r.status_code, 400)


# ---------------------------------------------------------------------------
# TestStageRoster
# ---------------------------------------------------------------------------

class TestStageRoster(TestCase):
    def setUp(self):
        self.school = _make_school()
        self.client = _client_for(self.school)
        self.section = _make_section(self.school.id)
        self.session_id, self.student_ids = _advance_to_students_loaded(
            self.client, self.school.id, self.section.id
        )

    def test_stage_success(self):
        changes = [{"student_id": self.student_ids[0], "action": "add"}]
        r = self.client.post(
            f"{BASE_URL}{self.session_id}/stage/",
            {"changes": changes},
            format="json",
            **_headers(self.school.id),
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["status"], "roster_staged")
        self.assertEqual(r.data["changes_count"], 1)

    def test_stage_invalid_action(self):
        changes = [{"student_id": self.student_ids[0], "action": "enroll"}]
        r = self.client.post(
            f"{BASE_URL}{self.session_id}/stage/",
            {"changes": changes},
            format="json",
            **_headers(self.school.id),
        )
        self.assertEqual(r.status_code, 400)

    def test_stage_empty_rejected(self):
        r = self.client.post(
            f"{BASE_URL}{self.session_id}/stage/",
            {"changes": []},
            format="json",
            **_headers(self.school.id),
        )
        self.assertEqual(r.status_code, 400)

    def test_stage_dedup_last_action_wins(self):
        sid = self.student_ids[0]
        changes = [
            {"student_id": sid, "action": "add"},
            {"student_id": sid, "action": "remove"},
        ]
        r = self.client.post(
            f"{BASE_URL}{self.session_id}/stage/",
            {"changes": changes},
            format="json",
            **_headers(self.school.id),
        )
        self.assertEqual(r.status_code, 200)
        # dedup keeps last → 1 change
        self.assertEqual(r.data["changes_count"], 1)


# ---------------------------------------------------------------------------
# TestCommit
# ---------------------------------------------------------------------------

class TestCommit(TestCase):
    def setUp(self):
        self.school = _make_school()
        self.client = _client_for(self.school)
        self.section = _make_section(self.school.id)

    def _staged_session_with_real_students(self, n_add=2, n_remove=0):
        """Create session staged with real Students."""
        add_students = [_make_student(self.school.id) for _ in range(n_add)]
        remove_students = []
        for _ in range(n_remove):
            s = _make_student(self.school.id)
            Enrollment.objects.create(section=self.section, student=s, school_id=self.school.id)
            remove_students.append(s)

        all_ids = [str(s.id) for s in add_students + remove_students]
        session_id = _advance_to_configured(self.client, self.school.id, self.section.id)
        self.client.post(
            f"{BASE_URL}{session_id}/load/",
            {"student_ids": all_ids},
            format="json",
            **_headers(self.school.id),
        )
        changes = (
            [{"student_id": str(s.id), "action": "add"} for s in add_students] +
            [{"student_id": str(s.id), "action": "remove"} for s in remove_students]
        )
        self.client.post(
            f"{BASE_URL}{session_id}/stage/",
            {"changes": changes},
            format="json",
            **_headers(self.school.id),
        )
        return session_id, add_students, remove_students

    def test_commit_adds_enrollments(self):
        session_id, add_students, _ = self._staged_session_with_real_students(n_add=2)
        r = self.client.post(
            f"{BASE_URL}{session_id}/commit/",
            {"confirm": True},
            format="json",
            **_headers(self.school.id),
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["status"], "committed")
        self.assertEqual(r.data["enrolled"], 2)
        self.assertEqual(r.data["removed"], 0)

    def test_commit_idempotent(self):
        session_id, _, _ = self._staged_session_with_real_students(n_add=1)
        r1 = self.client.post(
            f"{BASE_URL}{session_id}/commit/",
            {"confirm": True},
            format="json",
            **_headers(self.school.id),
        )
        r2 = self.client.post(
            f"{BASE_URL}{session_id}/commit/",
            {"confirm": True},
            format="json",
            **_headers(self.school.id),
        )
        self.assertEqual(r1.status_code, 200)
        self.assertEqual(r2.status_code, 200)

    def test_commit_remove_works(self):
        session_id, _, remove_students = self._staged_session_with_real_students(n_add=0, n_remove=1)
        r = self.client.post(
            f"{BASE_URL}{session_id}/commit/",
            {"confirm": True},
            format="json",
            **_headers(self.school.id),
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["removed"], 1)

    def test_commit_requires_confirm(self):
        session_id, _, _ = self._staged_session_with_real_students(n_add=1)
        r = self.client.post(
            f"{BASE_URL}{session_id}/commit/",
            {},
            format="json",
            **_headers(self.school.id),
        )
        self.assertEqual(r.status_code, 400)

    def test_commit_wrong_state(self):
        r_create = self.client.post(BASE_URL, **_headers(self.school.id))
        session_id = r_create.data["session_id"]
        r = self.client.post(
            f"{BASE_URL}{session_id}/commit/",
            {"confirm": True},
            format="json",
            **_headers(self.school.id),
        )
        self.assertEqual(r.status_code, 400)

    def test_commit_enrolled_count_correct(self):
        session_id, add_students, _ = self._staged_session_with_real_students(n_add=3)
        r = self.client.post(
            f"{BASE_URL}{session_id}/commit/",
            {"confirm": True},
            format="json",
            **_headers(self.school.id),
        )
        self.assertEqual(r.data["enrolled"], 3)

    def test_commit_mixed_add_and_remove(self):
        session_id, add_students, remove_students = self._staged_session_with_real_students(n_add=2, n_remove=1)
        r = self.client.post(
            f"{BASE_URL}{session_id}/commit/",
            {"confirm": True},
            format="json",
            **_headers(self.school.id),
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["enrolled"], 2)
        self.assertEqual(r.data["removed"], 1)


# ---------------------------------------------------------------------------
# TestVerify
# ---------------------------------------------------------------------------

class TestVerify(TestCase):
    def setUp(self):
        self.school = _make_school()
        self.client = _client_for(self.school)
        self.section = _make_section(self.school.id)

    def _committed_session(self):
        student = _make_student(self.school.id)
        session_id = _advance_to_configured(
            self.client, self.school.id, self.section.id
        )
        self.client.post(
            f"{BASE_URL}{session_id}/load/",
            {"student_ids": [str(student.id)]},
            format="json",
            **_headers(self.school.id),
        )
        self.client.post(
            f"{BASE_URL}{session_id}/stage/",
            {"changes": [{"student_id": str(student.id), "action": "add"}]},
            format="json",
            **_headers(self.school.id),
        )
        self.client.post(
            f"{BASE_URL}{session_id}/commit/",
            {"confirm": True},
            format="json",
            **_headers(self.school.id),
        )
        return session_id

    def test_verify_returns_200(self):
        session_id = self._committed_session()
        r = self.client.get(
            f"{BASE_URL}{session_id}/verify/",
            **_headers(self.school.id),
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["status"], "verified")

    def test_verify_returns_enrollment_count(self):
        session_id = self._committed_session()
        r = self.client.get(
            f"{BASE_URL}{session_id}/verify/",
            **_headers(self.school.id),
        )
        self.assertIn("enrollment_count", r.data)

    def test_verify_twice_is_ok(self):
        session_id = self._committed_session()
        r1 = self.client.get(f"{BASE_URL}{session_id}/verify/", **_headers(self.school.id))
        r2 = self.client.get(f"{BASE_URL}{session_id}/verify/", **_headers(self.school.id))
        self.assertEqual(r1.status_code, 200)
        self.assertEqual(r2.status_code, 200)

    def test_verify_wrong_state(self):
        r = self.client.post(BASE_URL, **_headers(self.school.id))
        session_id = r.data["session_id"]
        r = self.client.get(
            f"{BASE_URL}{session_id}/verify/",
            **_headers(self.school.id),
        )
        self.assertEqual(r.status_code, 400)

    def test_verify_contains_commit_result(self):
        session_id = self._committed_session()
        r = self.client.get(
            f"{BASE_URL}{session_id}/verify/",
            **_headers(self.school.id),
        )
        self.assertIn("enrolled", r.data)
        self.assertIn("removed", r.data)
