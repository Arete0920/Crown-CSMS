"""Academic compatibility pages respect verified family authority."""
import pytest
from rest_framework.test import APIClient
from core.models import School, UserAccount, UserRole
from households.models import Guardian, Household, Student
from academics.models import Course, Enrollment, Lesson, MasteryRecord, PublisherObjective, Section, TranscriptEntry, Unit
from academics.family_models import ClassroomDisclosure

pytestmark = pytest.mark.django_db


@pytest.fixture
def family_scope():
    school = School.objects.create(name="Fictional School")
    foreign = School.objects.create(name="Foreign Fictional School")
    parent = UserAccount.objects.create_user(username="family@example.test", email="family@example.test", school=school)
    UserRole.objects.create(user=parent, school=school, role_code="PARENT")
    home = Household.objects.create(school_id=school.id, name="Family")
    decoy_home = Household.objects.create(school_id=school.id, name="Unrelated Family")
    foreign_home = Household.objects.create(school_id=foreign.id, name="Foreign Family")
    guardian = Guardian.objects.create(account=parent, school_id=school.id, household=home,
                                       first_name="Sample", last_name="Parent", email="")
    Guardian.objects.create(school_id=school.id, household=decoy_home,
                            first_name="Email", last_name="Contact", email=parent.email)
    visible = Student.objects.create(school_id=school.id, household=home, first_name="Visible", last_name="Demo", grade_level="7")
    blocked = Student.objects.create(school_id=school.id, household=home, first_name="Restricted", last_name="Demo", grade_level="7")
    decoy = Student.objects.create(school_id=school.id, household=decoy_home, first_name="Unrelated", last_name="Demo", grade_level="7")
    outsider = Student.objects.create(school_id=foreign.id, household=foreign_home, first_name="Foreign", last_name="Demo", grade_level="7")
    ClassroomDisclosure.objects.create(school_id=school.id, student=blocked, guardian=guardian,
                                        allowed=False, reason="Fictional disclosure restriction", updated_by=parent)
    course = Course.objects.create(school_id=school.id, code="DEMO", name="Fictional Course")
    section = Section.objects.create(school_id=school.id, course=course, term="DEMO")
    unit = Unit.objects.create(school_id=school.id, course=course, title="Fictional Unit")
    lesson = Lesson.objects.create(school_id=school.id, unit=unit, title="Fictional Lesson")
    objective = PublisherObjective.objects.create(school_id=school.id, lesson=lesson, objective_code="DEMO", description="Sample objective")
    for child in (visible, blocked, decoy):
        Enrollment.objects.create(school_id=school.id, section=section, student=child)
        MasteryRecord.objects.create(school_id=school.id, student=child, objective=objective, mastery_level=3)
        TranscriptEntry.objects.create(school_id=school.id, student=child, course=course, final_letter_grade="A")
    foreign_course = Course.objects.create(school_id=foreign.id, code="FOREIGN", name="Foreign Course")
    foreign_unit = Unit.objects.create(school_id=foreign.id, course=foreign_course, title="Foreign Unit")
    foreign_lesson = Lesson.objects.create(school_id=foreign.id, unit=foreign_unit, title="Foreign Lesson")
    foreign_objective = PublisherObjective.objects.create(school_id=foreign.id, lesson=foreign_lesson,
                                                         objective_code="FOREIGN", description="Foreign sample objective")
    MasteryRecord.objects.create(school_id=foreign.id, student=outsider, objective=foreign_objective)
    TranscriptEntry.objects.create(school_id=foreign.id, student=outsider, course=foreign_course, final_letter_grade="B")
    client = APIClient()
    client.force_authenticate(parent)
    return dict(school=school, parent=parent, home=home, guardian=guardian, visible=visible,
                blocked=blocked, decoy=decoy, outsider=outsider, section=section, client=client)


def test_account_bound_parent_with_blank_contact_email_reads_only_disclosed_child(family_scope):
    f = family_scope
    response = f["client"].get("/api/v1/academics/parents/me/students/")
    assert response.status_code == 200
    assert [row["student_id"] for row in response.json()] == [str(f["visible"].id)]
    response = f["client"].get("/api/v1/academics/sections/")
    assert response.status_code == 200
    assert [row["section_id"] for row in response.json()["results"]] == [str(f["section"].id)]
    for key in ("blocked", "decoy", "outsider"):
        response = f["client"].get(f'/api/v1/academics/students/{f[key].id}/sections/')
        assert response.status_code == 404
    assert f["client"].get(f'/api/v1/academics/students/{f["visible"].id}/sections/').status_code == 200


def test_matching_email_without_account_binding_does_not_grant_family_access(family_scope):
    f = family_scope
    f["guardian"].account = None
    f["guardian"].save(update_fields=["account"])
    response = f["client"].get("/api/v1/academics/parents/me/students/")
    assert response.status_code == 200 and response.json() == []
    response = f["client"].get("/api/v1/academics/sections/")
    assert response.status_code == 200 and response.json()["results"] == []


@pytest.mark.parametrize("endpoint", ["mastery", "transcript-entries"])
def test_evidence_collections_exclude_unrelated_and_restricted_students(family_scope, endpoint):
    f = family_scope
    response = f["client"].get(f"/api/v1/academics/{endpoint}/")
    assert response.status_code == 200
    assert [row["student_id"] for row in response.json()["results"]] == [str(f["visible"].id)]
    for key in ("blocked", "decoy", "outsider"):
        response = f["client"].get(f'/api/v1/academics/{endpoint}/?student_id={f[key].id}')
        assert response.status_code == 200 and response.json()["results"] == []


def test_inactive_household_cannot_read_student_evidence(family_scope):
    f = family_scope
    f["home"].is_active = False
    f["home"].save(update_fields=["is_active"])
    assert f["client"].get("/api/v1/academics/parents/me/students/").json() == []
    for endpoint in ("mastery", "transcript-entries"):
        response = f["client"].get(f"/api/v1/academics/{endpoint}/")
        assert response.status_code == 200 and response.json()["results"] == []


@pytest.mark.parametrize("endpoint", ["mastery", "transcript-entries"])
def test_student_account_binding_reads_only_own_evidence(family_scope, endpoint):
    f = family_scope
    student_user = UserAccount.objects.create_user(username="student@example.test", school=f["school"])
    UserRole.objects.create(user=student_user, school=f["school"], role_code="STUDENT")
    f["visible"].account = student_user
    f["visible"].save(update_fields=["account"])
    f["client"].force_authenticate(student_user)
    response = f["client"].get(f"/api/v1/academics/{endpoint}/")
    assert response.status_code == 200
    assert [row["student_id"] for row in response.json()["results"]] == [str(f["visible"].id)]


@pytest.mark.parametrize("endpoint", ["mastery", "transcript-entries"])
def test_school_leader_reads_only_own_school_evidence(family_scope, endpoint):
    f = family_scope
    leader = UserAccount.objects.create_user(username="leader@example.test", school=f["school"])
    UserRole.objects.create(user=leader, school=f["school"], role_code="HEAD_OF_SCHOOL")
    f["client"].force_authenticate(leader)
    response = f["client"].get(f"/api/v1/academics/{endpoint}/")
    assert response.status_code == 200
    assert {row["student_id"] for row in response.json()["results"]} == {str(f[key].id) for key in ("visible", "blocked", "decoy")}
