"""Relationship-based classroom access; emails and staff flags are not grants."""
from django.db.models import Q
from rest_framework.exceptions import PermissionDenied
from core.models import UserRole
from households.models import Guardian, Student
from .models import Enrollment, Section, TeacherAssignment

LEADER_ROLES = {"ADMIN", "DIRECTOR", "HEAD_OF_SCHOOL", "head_of_school", "school_admin", "REGISTRAR"}
BOARD_ROLES = {"BOARD", "BOARD_MEMBER", "board", "school_board"}


def role_codes(user, school_id):
    return set(UserRole.objects.filter(user=user, school_id=school_id).values_list("role_code", flat=True))


def is_leader(user, school_id):
    return user.is_superuser or bool(role_codes(user, school_id) & LEADER_ROLES)


def taught_sections(user, school_id):
    qs = Section.objects.filter(school_id=school_id, course__school_id=school_id)
    staff = getattr(user, "staff", None)
    scope = Q(teacher_id=user.id)
    if staff is not None:
        assigned = TeacherAssignment.objects.filter(school_id=school_id, staff=staff).values("section_id")
        scope |= Q(id__in=assigned)
    return qs.filter(scope).distinct()


def related_students(user, school_id, *, audience):
    qs = Student.objects.filter(school_id=school_id, is_active=True,
                                household__school_id=school_id, household__is_active=True)
    if audience == "student":
        return qs.filter(account_id=user.id)
    households = Guardian.objects.filter(account_id=user.id, school_id=school_id,
                                          household__school_id=school_id,
                                          household__is_active=True).values("household_id")
    from .family_models import ClassroomDisclosure
    blocked = ClassroomDisclosure.objects.filter(school_id=school_id, guardian__account=user, allowed=False).values('student_id')
    return qs.filter(household_id__in=households).exclude(id__in=blocked)


def classroom_scope(user, school_id, audience):
    if not user.is_active:
        raise PermissionDenied("Active account required.")
    all_sections = Section.objects.filter(school_id=school_id, course__school_id=school_id)
    if audience == "admin" and is_leader(user, school_id):
        return all_sections, Student.objects.filter(school_id=school_id, is_active=True)
    if audience == "teacher":
        sections = taught_sections(user, school_id)
        if sections.exists() or role_codes(user, school_id) & {"TEACHER", "teacher"}:
            ids = Enrollment.objects.filter(school_id=school_id, section__in=sections,
                                             student__school_id=school_id).values("student_id")
            return sections, Student.objects.filter(id__in=ids, school_id=school_id, is_active=True)
    if audience in {"student", "parent"}:
        students = related_students(user, school_id, audience=audience)
        if students.exists():
            ids = Enrollment.objects.filter(school_id=school_id, student__in=students,
                                             section__school_id=school_id).values("section_id")
            return all_sections.filter(id__in=ids), students
    if audience == "board" and (is_leader(user, school_id) or role_codes(user, school_id) & BOARD_ROLES):
        return all_sections, Student.objects.none()
    raise PermissionDenied("No classroom relationship for this view.")


def accessible_enrollments(user, school_id):
    qs = Enrollment.objects.filter(school_id=school_id, section__school_id=school_id,
                                   student__school_id=school_id, student__is_active=True)
    if is_leader(user, school_id):
        return qs
    related = related_students(user, school_id, audience='parent').values('id')
    return qs.filter(Q(section__in=taught_sections(user, school_id)) |
                     Q(student__account_id=user.id) | Q(student_id__in=related)).distinct()
