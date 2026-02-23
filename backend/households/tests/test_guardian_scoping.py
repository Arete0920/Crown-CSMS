# backend/households/tests/test_guardian_scoping.py
#
# Layer C Phase 2 — PARENT-only guardian row scoping.
#
# Contract:
#   - When HOUSEHOLDS_GUARDIAN_SCOPE_ENABLED=True, a PARENT user sees ONLY
#     households where their email appears as a guardian.
#   - Non-PARENT roles (REGISTRAR, TEACHER) are NOT filtered by guardian
#     email — they see all school households as usual.
#   - A PARENT with no matching household gets an empty list, not someone
#     else's data.
#
# Uses Django TestCase + @override_settings (matches test_tenant_isolation.py).

import uuid

from django.test import Client, TestCase, override_settings
from core.models import School, UserAccount, UserRole
from households.models import Guardian, Household, Student


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _school(name="Scope Test School"):
    return School.objects.create(name=f"{name}-{uuid.uuid4()}")


def _user(email, school):
    return UserAccount.objects.create_user(
        username=f"user-{uuid.uuid4()}",
        email=email,
        password="Passw0rd!",
        school=school,
    )


def _assign_role(user, school, role_code):
    return UserRole.objects.create(user=user, school=school, role_code=role_code)


def _make_household(school, name, guardian_email):
    """Create a household with one primary guardian."""
    hh = Household.objects.create(school_id=school.id, name=name)
    Guardian.objects.create(
        school_id=school.id,
        household=hh,
        first_name="Test",
        last_name="Guardian",
        email=guardian_email,
        phone="555-0000",
        is_primary=True,
    )
    return hh


def _make_student(school, household, first_name):
    return Student.objects.create(
        school_id=school.id,
        household=household,
        first_name=first_name,
        last_name="Testson",
        grade_level="10",
        is_active=True,
    )


# ──────────────────────────────────────────────────────────────────────────────
# PARENT-scoped households tests
# ──────────────────────────────────────────────────────────────────────────────

@override_settings(
    HOUSEHOLDS_GUARDIAN_SCOPE_ENABLED=True,
    TENANT_HEADER_REQUIRED=True,
)
class TestParentGuardianScopingHouseholds(TestCase):
    """PARENT role users see only their own household via guardian email match."""

    def setUp(self):
        self.school = _school("Parent Own")
        self.parent_email = f"parent-{uuid.uuid4()}@example.com"
        self.other_email = f"other-{uuid.uuid4()}@example.com"

        self.parent_user = _user(self.parent_email, self.school)
        _assign_role(self.parent_user, self.school, "PARENT")

        self.own_hh = _make_household(self.school, "Own Family", self.parent_email)
        self.other_hh = _make_household(self.school, "Other Family", self.other_email)

    def test_parent_sees_own_household_only(self):
        c = Client()
        c.force_login(self.parent_user)
        r = c.get("/api/v1/households/", HTTP_X_SCHOOL_ID=str(self.school.id))

        self.assertEqual(r.status_code, 200)
        ids = [row["id"] for row in r.json()]
        self.assertIn(str(self.own_hh.id), ids, "PARENT must see their own household")
        self.assertEqual(len(ids), 1,
            f"PARENT must see exactly 1 household (own), got {len(ids)}")

    def test_parent_no_matching_household_gets_empty_list(self):
        school = _school("Parent Empty")
        parent_email = f"nobody-{uuid.uuid4()}@example.com"
        parent_user = _user(parent_email, school)
        _assign_role(parent_user, school, "PARENT")
        _make_household(school, "Stranger Family", f"stranger-{uuid.uuid4()}@example.com")

        c = Client()
        c.force_login(parent_user)
        r = c.get("/api/v1/households/", HTTP_X_SCHOOL_ID=str(school.id))

        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json(), [],
            "PARENT with no matching household must get empty list")


# ──────────────────────────────────────────────────────────────────────────────
# PARENT-scoped students tests
# ──────────────────────────────────────────────────────────────────────────────

@override_settings(
    HOUSEHOLDS_GUARDIAN_SCOPE_ENABLED=True,
    TENANT_HEADER_REQUIRED=True,
)
class TestParentGuardianScopingStudents(TestCase):
    """PARENT role users see only students in their own household."""

    def setUp(self):
        self.school = _school("Parent Students")
        self.parent_email = f"parent2-{uuid.uuid4()}@example.com"
        self.other_email = f"other2-{uuid.uuid4()}@example.com"

        self.parent_user = _user(self.parent_email, self.school)
        _assign_role(self.parent_user, self.school, "PARENT")

        self.own_hh = _make_household(self.school, "Own Family 2", self.parent_email)
        self.other_hh = _make_household(self.school, "Other Family 2", self.other_email)

        self.own_student = _make_student(self.school, self.own_hh, "Alice")
        self.other_student = _make_student(self.school, self.other_hh, "Bob")

    def test_parent_sees_own_students_only(self):
        c = Client()
        c.force_login(self.parent_user)
        r = c.get("/api/v1/students/", HTTP_X_SCHOOL_ID=str(self.school.id))

        self.assertEqual(r.status_code, 200)
        ids = [row["id"] for row in r.json()]
        self.assertIn(str(self.own_student.id), ids,
            "PARENT must see their own student")
        self.assertEqual(len(ids), 1,
            f"PARENT must see exactly 1 student, got {len(ids)}")


# ──────────────────────────────────────────────────────────────────────────────
# Non-PARENT roles must NOT be guardian-filtered
# ──────────────────────────────────────────────────────────────────────────────

@override_settings(
    HOUSEHOLDS_GUARDIAN_SCOPE_ENABLED=True,
    TENANT_HEADER_REQUIRED=True,
)
class TestNonParentRolesNotGuardianScoped(TestCase):
    """REGISTRAR and TEACHER see all school households even when guardian
    scope flag is enabled — the filter is PARENT-only."""

    def setUp(self):
        self.school = _school("Staff All")
        self.registrar_email = f"registrar-{uuid.uuid4()}@staff.example.com"
        self.teacher_email = f"teacher-{uuid.uuid4()}@staff.example.com"

        self.registrar = _user(self.registrar_email, self.school)
        _assign_role(self.registrar, self.school, "REGISTRAR")

        self.teacher = _user(self.teacher_email, self.school)
        _assign_role(self.teacher, self.school, "TEACHER")

        self.hh1 = _make_household(self.school, "Family Alpha",
            f"alpha-{uuid.uuid4()}@example.com")
        self.hh2 = _make_household(self.school, "Family Beta",
            f"beta-{uuid.uuid4()}@example.com")
        # Third household whose guardian email is the registrar's — must still be visible
        self.hh3 = _make_household(self.school, "Family Gamma", self.registrar_email)

    def test_registrar_sees_all_school_households(self):
        c = Client()
        c.force_login(self.registrar)
        r = c.get("/api/v1/households/", HTTP_X_SCHOOL_ID=str(self.school.id))

        self.assertEqual(r.status_code, 200)
        ids = [row["id"] for row in r.json()]
        for hh, label in ((self.hh1, "Alpha"), (self.hh2, "Beta"), (self.hh3, "Gamma")):
            self.assertIn(str(hh.id), ids,
                f"REGISTRAR must see household {label}")
        self.assertEqual(len(ids), 3,
            f"REGISTRAR must see all 3 households, got {len(ids)}")

    def test_teacher_sees_all_school_households(self):
        c = Client()
        c.force_login(self.teacher)
        r = c.get("/api/v1/households/", HTTP_X_SCHOOL_ID=str(self.school.id))

        self.assertEqual(r.status_code, 200)
        ids = [row["id"] for row in r.json()]
        for hh, label in ((self.hh1, "Alpha"), (self.hh2, "Beta"), (self.hh3, "Gamma")):
            self.assertIn(str(hh.id), ids,
                f"TEACHER must see household {label}")
        self.assertEqual(len(ids), 3,
            f"TEACHER must see all 3 households, got {len(ids)}")
