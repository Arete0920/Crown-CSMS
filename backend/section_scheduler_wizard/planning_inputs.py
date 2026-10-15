"""Pure Kairos planning-input checks; no database queries or publication writes.

Only authorized, school-scoped services may construct this data. An empty finding
list does not grant authority or certify source-data freshness. Avoid names,
addresses, disability records, or other direct PII in scheduling diagnostics.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

MAX_REQUESTS = 5000
MAX_TEACHER_RULES = 1000
MAX_CHOICES_PER_STUDENT = 32
MAX_UNAVAILABLE_PERIODS = 256
MAX_REPORTED_FINDINGS = 1000


@dataclass(frozen=True)
class TeacherPlanningRule:
    staff_id: str
    school_id: str
    academic_year_id: str
    term_code: str
    unavailable_period_ids: frozenset[str]
    max_instructional_minutes_per_cycle: int
    minimum_preparation_minutes_per_cycle: int


@dataclass(frozen=True)
class CourseChoice:
    course_id: str
    rank: int  # 1 is the student's highest elective preference


@dataclass(frozen=True)
class StudentCourseRequest:
    student_id: str  # verified canonical core.Student identity only
    school_id: str
    academic_year_id: str
    term_code: str
    identity_verified: bool
    required_course_ids: frozenset[str]
    elective_choices: tuple[CourseChoice, ...]


@dataclass(frozen=True)
class InputFinding:
    code: str
    item_index: int  # index for student requests; -1 for teacher policy
    message: str


def validate_planning_inputs(
    *,
    school_id: str,
    academic_year_id: str,
    term_code: str,
    known_staff_ids: frozenset[str],
    known_student_ids: frozenset[str],
    known_course_ids: frozenset[str],
    known_period_ids: frozenset[str],
    teacher_rules: Mapping[str, TeacherPlanningRule],
    student_requests: Sequence[StudentCourseRequest],
) -> tuple[InputFinding, ...]:
    """Refuse foreign, incomplete, ambiguous or inconsistent solver inputs.

    These checks are performed on immutable extracted projections, not database
    records. Source proof, eligibility, permission, and stability checks are the
    responsibility of the future authorized canonical-data adapter.
    """
    if not school_id or not academic_year_id or not term_code:
        return (InputFinding("MISSING_SCOPE", -1, "Explicit school, year and term required."),)
    if len(teacher_rules) > MAX_TEACHER_RULES or len(student_requests) > MAX_REQUESTS:
        return (InputFinding("INPUT_LIMIT", -1, "Planning input exceeds configured limits."),)
    findings: list[InputFinding] = []
    expected_scope = (school_id, academic_year_id, term_code)
    for key, rule in sorted(teacher_rules.items()):
        if key != rule.staff_id or rule.staff_id not in known_staff_ids or (
            rule.school_id, rule.academic_year_id, rule.term_code
        ) != expected_scope:
            findings.append(InputFinding("INVALID_TEACHER_SCOPE", -1, "Staff planning rule is not valid for this school and term."))
            continue
        if any(not isinstance(value, int) or isinstance(value, bool) or value < 0
               for value in (rule.max_instructional_minutes_per_cycle, rule.minimum_preparation_minutes_per_cycle)):
            findings.append(InputFinding("NEGATIVE_STAFF_LIMIT", -1, "Teacher workload and preparation limits must be nonnegative."))
        if len(rule.unavailable_period_ids) > MAX_UNAVAILABLE_PERIODS or not rule.unavailable_period_ids <= known_period_ids:
            findings.append(InputFinding("UNKNOWN_UNAVAILABLE_PERIOD", -1, "Unavailability must reference known current schedule periods."))
    seen_students: set[str] = set()
    for index, request in enumerate(student_requests):
        if request.student_id in seen_students:
            findings.append(InputFinding("DUPLICATE_STUDENT_REQUEST", index, "Student may submit only one request set per term."))
        seen_students.add(request.student_id)
        if request.student_id not in known_student_ids or (
            request.school_id, request.academic_year_id, request.term_code
        ) != expected_scope:
            findings.append(InputFinding("INVALID_STUDENT_SCOPE", index, "Student course request belongs to a different school or term."))
            continue
        if request.identity_verified is not True:
            findings.append(InputFinding("STUDENT_IDENTITY_UNVERIFIED", index, "A verified canonical student identity is required."))
        if not request.required_course_ids <= known_course_ids:
            findings.append(InputFinding("UNKNOWN_REQUIRED_COURSE", index, "A required course is not in the authorized catalog."))
        if len(request.elective_choices) > MAX_CHOICES_PER_STUDENT:
            findings.append(InputFinding("TOO_MANY_ELECTIVES", index, "Elective request limit exceeded."))
            continue
        elective_course_ids = [choice.course_id for choice in request.elective_choices]
        ranks = [choice.rank for choice in request.elective_choices]
        if any(course_id not in known_course_ids for course_id in elective_course_ids):
            findings.append(InputFinding("UNKNOWN_ELECTIVE", index, "An elective is not in the authorized catalog."))
        if len(set(elective_course_ids)) != len(elective_course_ids) or set(elective_course_ids) & request.required_course_ids:
            findings.append(InputFinding("DUPLICATE_COURSE_CHOICE", index, "Course selections must be distinct across required and elective requests."))
        if any(not isinstance(rank, int) or isinstance(rank, bool) for rank in ranks) or sorted(ranks) != list(range(1, len(ranks) + 1)):
            findings.append(InputFinding("INVALID_RANKS", index, "Elective ranks must start at 1, be unique and consecutive."))
        if len(findings) >= MAX_REPORTED_FINDINGS:
            return tuple(findings[:MAX_REPORTED_FINDINGS]) + (InputFinding("FINDINGS_TRUNCATED", -1, "Additional findings omitted; correct and retry."),)
    return tuple(findings)
