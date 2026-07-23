"""
Layer C scoping contract tests.

These tests prove the row- and field-scoping rules defined in core/scoping.py
fire correctly for real model relationships. They are NOT unit tests of the
filter strings — they run against the actual database.

Rules:
- Every wired pathway must have a passing test here.
- Every stubbed pathway (qs.none()) is documented as BLOCKED with reason.
- If a test is added here, CROWN_LAYER_C_SCOPING_MATRIX.md must be updated.
- Never proxy role logic through view tests — test scoping.py directly.
"""
import uuid
from unittest.mock import MagicMock

from django.test import TestCase

from core.models import (
    Family,
    Guardian as CoreGuardian,
    School,
    UserAccount,
)
from core.scoping import (
    DOMAIN_FINANCIAL,
    DOMAIN_FINANCIAL_AID,
    DOMAIN_STUDENTS,
    FieldScope,
    get_field_scope,
    scope_queryset,
    scope_serializer_fields,
    scoped_serializer_context,
)
from households.models import Guardian as HouseholdsGuardian, Household, Student
from academics.models import Course, Enrollment as AcademicEnrollment, Section
from financial_aid.models import FinancialAidApplication
TEST_AUTH_SECRET = "TestAuthSecret-LocalOnly"



# ---------------------------------------------------------------------------
# Test: Teacher → Students via Section → Enrollment
# Status: IMPLEMENTED (academics.Enrollment.section.teacher pathway)
# ---------------------------------------------------------------------------

class TestScopingStudentsTeacher(TestCase):
    def setUp(self):
        self.school_id = uuid.uuid4()
        self.school = School.objects.create(
            id=self.school_id,
            name="Teacher Scoping Test School",
        )

        # Teacher with a section and one enrolled student.
        self.teacher = UserAccount.objects.create_user(
            username="teacher_scope_test",
            email="teacher_scope_test@example.com",
            password=TEST_AUTH_SECRET,
            school=self.school,
        )
        self.teacher.role = "TEACHER"  # fallback for resolve_role (no UserRole record)

        # Second teacher with no sections — must see nothing.
        self.unassigned_teacher = UserAccount.objects.create_user(
            username="unassigned_teacher_scope_test",
            email="unassigned_teacher_scope_test@example.com",
            password=TEST_AUTH_SECRET,
            school=self.school,
        )
        self.unassigned_teacher.role = "TEACHER"

        hh = Household.objects.create(school_id=self.school_id, name="Smith Family")
        self.enrolled_student = Student.objects.create(
            school_id=self.school_id, household=hh,
            first_name="Alice", last_name="Smith",
        )
        self.unenrolled_student = Student.objects.create(
            school_id=self.school_id, household=hh,
            first_name="Bob", last_name="Smith",
        )

        course = Course.objects.create(
            school_id=self.school_id, code="MATH001", name="Math"
        )
        section = Section.objects.create(
            school_id=self.school_id,
            course=course,
            term="2026-SPRING",
            teacher=self.teacher,
        )
        AcademicEnrollment.objects.create(
            school_id=self.school_id,
            section=section,
            student=self.enrolled_student,
        )

    def test_teacher_sees_only_enrolled_students(self):
        qs = Student.objects.filter(school_id=self.school_id)
        result = scope_queryset(self.teacher, qs, DOMAIN_STUDENTS)
        ids = set(result.values_list("id", flat=True))
        self.assertIn(self.enrolled_student.id, ids)
        self.assertNotIn(self.unenrolled_student.id, ids)

    def test_teacher_with_no_sections_sees_nothing(self):
        qs = Student.objects.filter(school_id=self.school_id)
        result = scope_queryset(self.unassigned_teacher, qs, DOMAIN_STUDENTS)
        self.assertEqual(result.count(), 0)


# ---------------------------------------------------------------------------
# Test: Parent → Students via Guardian.email → Household
# Status: IMPLEMENTED (household__guardians__email__iexact)
# ---------------------------------------------------------------------------

class TestScopingStudentsParent(TestCase):
    def setUp(self):
        self.school_id = uuid.uuid4()

        self.parent = UserAccount.objects.create_user(
            username="parent_scope_test", password=TEST_AUTH_SECRET, email="mama@family.com"
        )
        self.parent.role = "PARENT"

        # Own household — guardian email matches parent user email.
        own_hh = Household.objects.create(school_id=self.school_id, name="Own Family")
        HouseholdsGuardian.objects.create(
            school_id=self.school_id,
            household=own_hh,
            first_name="Mama", last_name="Smith",
            email="mama@family.com",
        )
        self.own_student = Student.objects.create(
            school_id=self.school_id, household=own_hh,
            first_name="Child", last_name="Smith",
        )

        # Another household — must not be visible.
        other_hh = Household.objects.create(school_id=self.school_id, name="Other Family")
        self.other_student = Student.objects.create(
            school_id=self.school_id, household=other_hh,
            first_name="Other", last_name="Jones",
        )

    def test_parent_sees_only_own_household_students(self):
        qs = Student.objects.filter(school_id=self.school_id)
        result = scope_queryset(self.parent, qs, DOMAIN_STUDENTS)
        ids = set(result.values_list("id", flat=True))
        self.assertIn(self.own_student.id, ids)
        self.assertNotIn(self.other_student.id, ids)

    def test_parent_email_match_is_case_insensitive(self):
        """Guardian email stored as 'mama@family.com', user.email as 'MAMA@Family.com'"""
        case_parent = UserAccount.objects.create_user(
            username="case_parent_scope_test", password=TEST_AUTH_SECRET,
            email="MAMA@Family.com",
        )
        case_parent.role = "PARENT"
        qs = Student.objects.filter(school_id=self.school_id)
        result = scope_queryset(case_parent, qs, DOMAIN_STUDENTS)
        self.assertIn(self.own_student.id, set(result.values_list("id", flat=True)))

    def test_parent_with_no_guardian_record_sees_nothing(self):
        orphan = UserAccount.objects.create_user(
            username="orphan_parent_scope_test", password=TEST_AUTH_SECRET,
            email="no.guardian@example.com",
        )
        orphan.role = "PARENT"
        qs = Student.objects.filter(school_id=self.school_id)
        self.assertEqual(scope_queryset(orphan, qs, DOMAIN_STUDENTS).count(), 0)


# ---------------------------------------------------------------------------
# Test: Parent → FinancialAidApplication via Guardian.email → household_id
# Status: IMPLEMENTED (lazy households.Guardian lookup by email → household_id__in)
# ---------------------------------------------------------------------------

class TestScopingFinancialAidParent(TestCase):
    def setUp(self):
        self.school_id = uuid.uuid4()

        self.parent = UserAccount.objects.create_user(
            username="aid_parent_scope_test", password=TEST_AUTH_SECRET,
            email="guardian@family.com",
        )
        self.parent.role = "PARENT"

        # Own household — guardian email matches.
        own_hh = Household.objects.create(school_id=self.school_id, name="Own Family")
        HouseholdsGuardian.objects.create(
            school_id=self.school_id,
            household=own_hh,
            first_name="Guardian", last_name="Smith",
            email="guardian@family.com",
        )

        # Applications: one matching, one from a random household.
        self.own_app = FinancialAidApplication.objects.create(
            school_id=self.school_id,
            household_id=own_hh.id,
            academic_year="2025-2026",
        )
        self.other_app = FinancialAidApplication.objects.create(
            school_id=self.school_id,
            household_id=uuid.uuid4(),
            academic_year="2025-2026",
        )

    def test_parent_sees_only_own_household_applications(self):
        qs = FinancialAidApplication.objects.filter(school_id=self.school_id)
        result = scope_queryset(self.parent, qs, DOMAIN_FINANCIAL_AID)
        ids = set(result.values_list("id", flat=True))
        self.assertIn(self.own_app.id, ids)
        self.assertNotIn(self.other_app.id, ids)

    def test_parent_with_no_guardian_record_sees_nothing(self):
        ghost = UserAccount.objects.create_user(
            username="ghost_aid_scope_test", password=TEST_AUTH_SECRET,
            email="nobody@void.com",
        )
        ghost.role = "PARENT"
        qs = FinancialAidApplication.objects.filter(school_id=self.school_id)
        self.assertEqual(scope_queryset(ghost, qs, DOMAIN_FINANCIAL_AID).count(), 0)


# ---------------------------------------------------------------------------
# Test: Parent → LedgerEntry via user.guardian.family
# Status: IMPLEMENTED (qs.filter(family=user.guardian.family))
# NOTE: Uses mock QuerySet — real DB test deferred until LedgerEntry models are
# stable (ChartAccount + JournalBatch FK chain complicates test setup).
# Rename to test_scope_financial_parent_family once DB test is feasible.
# ---------------------------------------------------------------------------

class TestScopingFinancialParentFamily(TestCase):
    def setUp(self):
        school = School.objects.create(name="Test School FIN")
        self.family_a = Family.objects.create(school=school, family_name="Family A")
        self.family_b = Family.objects.create(school=school, family_name="Family B")
        self.guardian = CoreGuardian.objects.create(
            school=school,
            family=self.family_a,
            first_name="Core", last_name="Guardian",
            email="core@family.com",
            relationship="MOTHER",
        )

        # Link guardian via DB update so guardian_id is persisted, then role attribute.
        self.parent = UserAccount.objects.create_user(
            username="fin_parent_scope_test", password=TEST_AUTH_SECRET,
        )
        UserAccount.objects.filter(pk=self.parent.pk).update(guardian=self.guardian)
        self.parent.refresh_from_db()
        self.parent.role = "PARENT"

    def test_scope_financial_parent_family__contract_only(self):
        """Contract: scope_queryset calls qs.filter(family=<parent's family>).
        Using mock qs — real model test deferred until LedgerEntry FK chain stabilizes.
        """
        mock_qs = MagicMock()
        mock_filtered = MagicMock()
        mock_qs.filter.return_value = mock_filtered

        result = scope_queryset(self.parent, mock_qs, DOMAIN_FINANCIAL)

        mock_qs.filter.assert_called_once_with(family=self.family_a)
        self.assertEqual(result, mock_filtered)

    def test_scope_financial_parent_no_guardian__contract_only(self):
        """Contract: parent with no guardian FK gets qs.none(), not an exception.
        Using mock qs — consistent with above.
        """
        orphan = UserAccount.objects.create_user(
            username="fin_orphan_scope_test", password=TEST_AUTH_SECRET,
        )
        orphan.role = "PARENT"
        mock_qs = MagicMock()

        _ = scope_queryset(orphan, mock_qs, DOMAIN_FINANCIAL)

        mock_qs.filter.assert_not_called()


# ---------------------------------------------------------------------------
# Test: Unknown domain → deny by default
# Status: FROZEN BEHAVIOR — must always return qs.none(), never raise
# ---------------------------------------------------------------------------

class TestScopingDefaultDenyUnknownDomain(TestCase):
    def test_unknown_domain_returns_empty_queryset(self):
        user = UserAccount.objects.create_user(
            username="unknown_domain_scope_test", password=TEST_AUTH_SECRET,
        )
        qs = Student.objects.all()
        result = scope_queryset(user, qs, "nonexistent_domain_xyz")
        # Must return an empty queryset, not None, not an exception.
        self.assertEqual(list(result), [])

    def test_empty_domain_string_returns_empty_queryset(self):
        user = UserAccount.objects.create_user(
            username="empty_domain_scope_test", password=TEST_AUTH_SECRET,
        )
        qs = Student.objects.all()
        result = scope_queryset(user, qs, "")
        self.assertEqual(list(result), [])


# ---------------------------------------------------------------------------
# Test: Field scope — serializer pruning
# ---------------------------------------------------------------------------

class TestScopingFieldScope(TestCase):
    """
    Prove that scope_serializer_fields correctly prunes restricted fields.
    Uses a minimal mock serializer (a dict-like with .fields attribute).
    """

    class _MockFields(dict):
        def pop(self, key, default=None):
            return super().pop(key, default)

    class _MockSerializer:
        def __init__(self, fields, context=None):
            self.fields = TestScopingFieldScope._MockFields(
                {f: object() for f in fields}
            )
            self.context = context or {}

    def _make_serializer(self, fields, domain):
        return self._MockSerializer(fields, context={"crown_domain": domain})

    def test_teacher_student_fields_are_pruned(self):
        teacher = UserAccount.objects.create_user(
            username="field_teacher_test", password=TEST_AUTH_SECRET
        )
        teacher.role = "TEACHER"
        ser = self._make_serializer(
            ["id", "first_name", "last_name", "ssn", "counseling_notes", "grade_level"],
            DOMAIN_STUDENTS,
        )
        scope_serializer_fields(teacher, ser)
        remaining = set(ser.fields.keys())
        self.assertIn("id", remaining)
        self.assertIn("first_name", remaining)
        self.assertIn("grade_level", remaining)
        self.assertNotIn("ssn", remaining)
        self.assertNotIn("counseling_notes", remaining)

    def test_director_student_fields_unchanged(self):
        director = UserAccount.objects.create_user(
            username="field_director_test", password=TEST_AUTH_SECRET
        )
        director.role = "HEAD_OF_SCHOOL"
        all_fields = ["id", "first_name", "last_name", "ssn", "counseling_notes", "grade_level"]
        ser = self._make_serializer(all_fields, DOMAIN_STUDENTS)
        scope_serializer_fields(director, ser)
        # Director gets __all__ — no fields removed (except explicit deny, which is empty for head)
        for f in all_fields:
            self.assertIn(f, ser.fields)

    def test_missing_domain_in_context_clears_all_fields(self):
        user = UserAccount.objects.create_user(
            username="field_nodomain_test", password=TEST_AUTH_SECRET
        )
        ser = self._MockSerializer(
            ["id", "first_name", "secret"],
            context={},   # no crown_domain
        )
        scope_serializer_fields(user, ser)
        self.assertEqual(len(ser.fields), 0)


