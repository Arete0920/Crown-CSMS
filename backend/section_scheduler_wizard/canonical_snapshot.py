"""Internal read-only Kairos projection over verified canonical records.

This service is NOT a publishing API. It checks human school-scoped permission,
does not infer student identity, and refuses ambiguous academic authority.
Returned fingerprints are advisory: publication must re-check transactional state.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from json import dumps
from types import MappingProxyType
from typing import Mapping
from uuid import UUID

from rest_framework.exceptions import PermissionDenied, ValidationError

from academics.models import Course, Enrollment, Section, TeacherAssignment, Term
from bell_schedule_wizard.models import BellSchedule, DayTemplate, PeriodBlock
from core.models import AcademicYear, School, StudentIdentityLink
from core.permissions import user_has_permission
from room_setup_wizard.models import Room
from .preflight import PeriodInput, RoomInput, SectionInput

MAX_SECTIONS = 2000
MAX_ENROLLMENTS = 20000
MAX_ASSIGNMENTS = 10000
MAX_PERIODS = 1000
MAX_ROOMS = 1000
MAX_COURSES = 5000


@dataclass(frozen=True)
class CanonicalPlanningSnapshot:
    school_id: str
    academic_year_id: str
    term_code: str
    section_inputs: Mapping[str, SectionInput]
    period_inputs: Mapping[str, PeriodInput]
    room_inputs: Mapping[str, RoomInput]
    catalog_course_ids: frozenset[str]
    verified_student_ids: frozenset[str]
    assigned_staff_ids: frozenset[str]
    source_fingerprint: str


def _minute(value):
    if value.second or value.microsecond:
        raise ValidationError("Time blocks must use minute precision.")
    return value.hour * 60 + value.minute


def build_canonical_planning_snapshot(*, actor, school_id, academic_year_id, term_code):
    """Build a bounded, school-authorized projection; never write canonical data."""
    if not school_id or not academic_year_id or not term_code:
        raise ValidationError("Explicit school, academic year and term are required.")
    try:
        school_id = UUID(str(school_id))
        academic_year_id = UUID(str(academic_year_id))
    except (TypeError, ValueError, AttributeError):
        raise ValidationError("School and year IDs must be UUIDs.") from None

    if not getattr(actor, "is_authenticated", False) or not getattr(actor, "is_active", False):
        raise PermissionDenied("Active school principal required.")
    school = School.objects.filter(pk=school_id, is_active=True).first()
    if school is None or not user_has_permission(actor, "scheduling.view", school=school):
        raise PermissionDenied("School scheduling access required.")
    if not AcademicYear.objects.filter(pk=academic_year_id, school_id=school_id).exists():
        raise ValidationError("The year does not belong to this school.")

    terms = list(Term.objects.filter(school_id=school_id, academic_year_id=academic_year_id,
                                      code=term_code, active=True)[:2])
    if len(terms) != 1:
        raise ValidationError("Exactly one active canonical term is required.")
    schedules = list(BellSchedule.objects.filter(school_id=school_id,
                                                  academic_year_id=academic_year_id,
                                                  is_active=True)[:2])
    if len(schedules) != 1:
        raise ValidationError("Exactly one active bell schedule is required.")
    schedule = schedules[0]

    # Rows with no academic-year authority cannot be assigned to the requested year.
    if Section.objects.filter(school_id=school_id, term=term_code).exclude(term_ref_id=terms[0].id).exists():
        raise ValidationError("Sections with missing, stale or foreign-year term links require reconciliation.")
    sections_raw = list(Section.objects.filter(
        school_id=school_id, term_ref_id=terms[0].id, term=term_code
    ).select_related("course").order_by("id")[:MAX_SECTIONS + 1])
    if len(sections_raw) > MAX_SECTIONS:
        raise ValidationError("Too many sections for a single snapshot.")
    if any(s.course.school_id != school_id for s in sections_raw):
        raise ValidationError("Section references a foreign course.")
    section_ids = [s.id for s in sections_raw]

    # Never silently omit a record that points into the selected section set.
    if Enrollment.objects.filter(section_id__in=section_ids).exclude(school_id=school_id).exists():
        raise ValidationError("Foreign-scoped enrollment needs reconciliation.")
    enrollments = list(Enrollment.objects.filter(
        school_id=school_id, section_id__in=section_ids
    ).select_related("student__household")[:MAX_ENROLLMENTS + 1])
    if len(enrollments) > MAX_ENROLLMENTS:
        raise ValidationError("Too many course enrollments.")
    if any(e.student.school_id != school_id or e.student.household.school_id != school_id
           or not e.student.is_active for e in enrollments):
        raise ValidationError("An enrolled compatibility student is foreign or inactive.")

    compat_ids = {e.student_id for e in enrollments}
    links = list(StudentIdentityLink.objects.filter(
        school_id=school_id, compatibility_student_id__in=compat_ids,
        verification_status=StudentIdentityLink.STATUS_VERIFIED
    ).select_related("core_student__family")[:MAX_ENROLLMENTS + 1])
    crosswalk = {link.compatibility_student_id: link for link in links}
    if len(links) != len(compat_ids) or len(crosswalk) != len(compat_ids):
        raise ValidationError("Every enrolled student requires one verified canonical identity.")
    source_codes = {code for code, _ in StudentIdentityLink.SOURCE_CHOICES}
    if any(
        not link.evidence_reference.strip()
        or link.source not in source_codes
        or link.core_student.school_id != school_id
        or link.core_student.family.school_id != school_id
        or link.core_student.status != "ACTIVE"
        for link in links
    ):
        raise ValidationError("Student identity evidence or tenant status is invalid.")

    if TeacherAssignment.objects.filter(section_id__in=section_ids).exclude(school_id=school_id).exists():
        raise ValidationError("Foreign-scoped teaching assignment needs reconciliation.")
    teachers = list(TeacherAssignment.objects.filter(
        school_id=school_id, section_id__in=section_ids
    ).select_related("staff")[:MAX_ASSIGNMENTS + 1])
    if len(teachers) > MAX_ASSIGNMENTS:
        raise ValidationError("Too many teaching assignments.")
    if any(t.staff.school_id != school_id or t.staff.status != "ACTIVE" for t in teachers):
        raise ValidationError("Teaching staff is foreign or inactive.")

    by_student = {s.id: set() for s in sections_raw}
    by_staff = {s.id: set() for s in sections_raw}
    for row in enrollments:
        by_student[row.section_id].add(str(crosswalk[row.student_id].core_student_id))
    for row in teachers:
        by_staff[row.section_id].add(str(row.staff_id))
    sections = {
        str(s.id): SectionInput(
            str(s.id), str(school_id), str(academic_year_id), term_code,
            frozenset(by_staff[s.id]), frozenset(by_student[s.id]), True
        ) for s in sections_raw
    }

    templates = list(DayTemplate.objects.filter(schedule_id=schedule.id))
    if not templates:
        raise ValidationError("Active bell schedule has no day templates.")
    period_rows = list(PeriodBlock.objects.filter(
        template_id__in=[t.id for t in templates]
    ).select_related("template")[:MAX_PERIODS + 1])
    if len(period_rows) > MAX_PERIODS or not period_rows or not any(p.is_instructional for p in period_rows):
        raise ValidationError("Bell schedule periods are absent or exceed the limit.")
    periods = {}
    for p in period_rows:
        start, end = _minute(p.start_time), _minute(p.end_time)
        if start >= end:
            raise ValidationError("Bell schedule contains an invalid period.")
        k = str(p.id)
        periods[k] = PeriodInput(k, str(school_id), str(academic_year_id),
                                 str(p.template_id), start, end, p.is_instructional)

    room_rows = list(Room.objects.filter(
        school_id=school_id, is_active=True
    ).order_by("id")[:MAX_ROOMS + 1])
    if len(room_rows) > MAX_ROOMS:
        raise ValidationError("Too many active rooms.")
    rooms = {str(r.id): RoomInput(str(r.id), str(school_id), r.capacity) for r in room_rows}
    course_rows = list(Course.objects.filter(school_id=school_id).values_list(
        "id", flat=True
    )[:MAX_COURSES + 1])
    if len(course_rows) > MAX_COURSES:
        raise ValidationError("Too many catalog courses.")
    catalog = frozenset(str(c) for c in course_rows)

    # Fingerprint only opaque IDs and scheduling-relevant values, never names or PII.
    course_by_section = {str(section.id): str(section.course_id) for section in sections_raw}
    payload = {
        "scope": [str(school_id), str(academic_year_id), term_code, str(schedule.id)],
        "sections": [
            [key, course_by_section[key],
             sorted(value.teacher_ids), sorted(value.student_ids)]
            for key, value in sorted(sections.items())
        ],
        "periods": [
            [key, p.template_id, p.start_minute, p.end_minute, p.instructional]
            for key, p in sorted(periods.items())
        ],
        "rooms": [[key, r.capacity] for key, r in sorted(rooms.items())],
        "catalog": sorted(catalog),
    }
    fingerprint = sha256(dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return CanonicalPlanningSnapshot(
        str(school_id), str(academic_year_id), term_code,
        MappingProxyType(sections), MappingProxyType(periods), MappingProxyType(rooms),
        catalog, frozenset(str(link.core_student_id) for link in links),
        frozenset(str(t.staff_id) for t in teachers), fingerprint
    )
