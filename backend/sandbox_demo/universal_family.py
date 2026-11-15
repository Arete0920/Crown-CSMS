"""Canonical family/account links for the fictional presenter, not portal bypasses."""
import uuid
from datetime import date

from academics.models import AssignmentCategory, Course, Enrollment, Section, TeacherAssignment, Term
from core.models import AcademicYear, Enrollment as CoreEnrollment, GradeLevel, HouseholdFamilyLink, Student, StudentIdentityLink, UserAccount
from households.models import Guardian, Household, Student as PortalStudent
from .student_self_service import COURSE_CODE, STUDENT_NUMBER, TERM_CODE
from .universal_identity import presenter_username


def seed_presenter_family(school):
    from .universal_demo import _owned_school
    from .universal_runtime import require_presenter_runtime
    from django.core.management.base import CommandError
    require_presenter_runtime()
    owned = _owned_school()
    if owned is None or owned.pk != school.pk:
        raise CommandError("Presenter family requires its owned fictional school.")
    parent = UserAccount.objects.select_related("guardian__family").get(school=school, username=presenter_username("parent", school.pk))
    learner = UserAccount.objects.get(school=school, username=presenter_username("student", school.pk))
    teacher = UserAccount.objects.get(school=school, username=presenter_username("teacher", school.pk))
    guardian = parent.guardian
    if guardian is None or guardian.school_id != school.pk or guardian.family.school_id != school.pk:
        raise CommandError("Presenter parent requires a same-school canonical family.")
    household = Household.objects.create(school_id=school.pk, name=guardian.family.family_name)
    HouseholdFamilyLink.objects.create(school=school, household_id=household.pk,
        family=guardian.family, source=HouseholdFamilyLink.SOURCE_MANUAL)
    Guardian.objects.create(school_id=school.pk, household=household, account=parent,
                            first_name=guardian.first_name, last_name=guardian.last_name,
                            email=parent.email, is_primary=True)
    stable_id = uuid.uuid5(school.pk, "presenter:avery-reed")
    portal_student = PortalStudent.objects.create(id=stable_id, school_id=school.pk,
        household=household, account=learner, first_name=learner.first_name,
        last_name=learner.last_name, grade_level="7")
    grade = GradeLevel.objects.get(school=school, code="7")
    student = Student.objects.create(id=stable_id, school=school, family=guardian.family,
        student_number=STUDENT_NUMBER, first_name=learner.first_name, last_name=learner.last_name,
        dob=date(2013, 4, 12), current_grade_level=grade, status="ACTIVE")
    StudentIdentityLink.objects.create(school=school, core_student=student,
        compatibility_student=portal_student, source=StudentIdentityLink.SOURCE_RECONCILIATION,
        verification_status=StudentIdentityLink.STATUS_VERIFIED,
        evidence_reference="fictional:universal-presenter:canonical-family:v1")
    year = AcademicYear.objects.get(school=school, is_current=True)
    CoreEnrollment.objects.create(school=school, student=student, academic_year=year,
                                  grade_level=grade, start_date=year.start_date, status="ENROLLED")
    term = Term.objects.create(school_id=school.pk, academic_year=year, code=TERM_CODE,
                               name="Fall 2026", school_year=year.name)
    course = Course.objects.create(school_id=school.pk, code=COURSE_CODE, name="Grade 7 English Language Arts")
    section = Section.objects.create(school_id=school.pk, course=course, term=TERM_CODE,
                                      term_ref=term, teacher=teacher, teacher_name="Eleanor Lower", grade_band="7")
    TeacherAssignment.objects.create(school_id=school.pk, section=section, staff=teacher.staff)
    enrollment = Enrollment.objects.create(school_id=school.pk, section=section, student=portal_student)
    category = AssignmentCategory.objects.create(school_id=school.pk, section=section, name="Classwork")
    return {"family_student_id": str(stable_id), "family_section_id": str(section.pk),
            "family_enrollment_id": str(enrollment.pk), "family_category_id": str(category.pk)}


def archive_presenter_classroom():
    """Reset visible practice work while retaining immutable submission history."""
    from django.core.management.base import CommandError
    from django.db import transaction
    from academics.models import Assignment
    from .models import SandboxEvent
    from .universal_demo import _owned_school
    from .universal_runtime import require_presenter_runtime
    require_presenter_runtime()
    with transaction.atomic():
        school = _owned_school()
        if school is None:
            raise CommandError("An owned presenter school is required for classroom reset.")
        rows = list(Assignment.objects.select_for_update().filter(school_id=school.pk, is_published=True))
        for assignment in rows:
            # Normal model validation rechecks section/category ownership. No
            # deletion or rewrite of immutable grade/submission evidence.
            assignment.is_published = False
            assignment.save(update_fields=["is_published"])
        SandboxEvent.objects.create(event="universal_presenter_classroom_archived_v1",
            school=str(school.pk), track="school", guidance="ops", persona="operator", step=len(rows))
    return {"mode": "CLASSROOM_ARCHIVED", "school_id": str(school.pk),
            "assignments_archived": len(rows), "history_retained": True, "release_certified": False}
