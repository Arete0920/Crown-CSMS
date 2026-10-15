from dataclasses import replace

from section_scheduler_wizard.planning_inputs import (
    MAX_REPORTED_FINDINGS, CourseChoice, StudentCourseRequest, TeacherPlanningRule, validate_planning_inputs,
)


def fixture():
    teacher = TeacherPlanningRule("t1", "school", "year", "S1", frozenset({"p2"}), 1200, 200)
    student = StudentCourseRequest("s1", "school", "year", "S1", True, frozenset({"english"}), (CourseChoice("art", 1), CourseChoice("music", 2)))
    return teacher, student


def check(*, teachers=None, requests=None, school="school"):
    teacher, student = fixture()
    return validate_planning_inputs(
        school_id=school, academic_year_id="year", term_code="S1",
        known_staff_ids=frozenset({"t1"}), known_student_ids=frozenset({"s1", "s2"}),
        known_course_ids=frozenset({"english", "art", "music"}), known_period_ids=frozenset({"p1", "p2"}),
        teacher_rules={"t1": teacher} if teachers is None else teachers,
        student_requests=[student] if requests is None else requests,
    )


def codes(items):
    return {x.code for x in items}


def test_valid_inputs_are_accepted():
    assert check() == ()


def test_foreign_school_is_rejected():
    assert codes(check(school="other")) == {"INVALID_TEACHER_SCOPE", "INVALID_STUDENT_SCOPE"}


def test_unknown_teacher_mapping_key_and_period_rejected():
    t, _ = fixture()
    assert codes(check(teachers={"alias": replace(t, unavailable_period_ids=frozenset({"p4"}))})) == {"INVALID_TEACHER_SCOPE"}
    assert codes(check(teachers={"t1": replace(t, unavailable_period_ids=frozenset({"p4"}))})) == {"UNKNOWN_UNAVAILABLE_PERIOD"}


def test_negative_workload_rejected():
    t, _ = fixture()
    assert "NEGATIVE_STAFF_LIMIT" in codes(check(teachers={"t1": replace(t, max_instructional_minutes_per_cycle=-1)}))


def test_unverified_student_link_rejected():
    _, r = fixture()
    assert codes(check(requests=[replace(r, identity_verified=False)])) == {"STUDENT_IDENTITY_UNVERIFIED"}


def test_unknown_required_and_elective_courses_rejected():
    _, r = fixture()
    q = replace(r, required_course_ids=frozenset({"unknown"}), elective_choices=(CourseChoice("unknown2", 1),))
    assert codes(check(requests=[q])) == {"UNKNOWN_REQUIRED_COURSE", "UNKNOWN_ELECTIVE"}


def test_duplicate_and_non_consecutive_ranked_electives_rejected():
    _, r = fixture()
    q = replace(r, elective_choices=(CourseChoice("art", 2), CourseChoice("art", 2), CourseChoice("music", 4)))
    assert codes(check(requests=[q])) == {"DUPLICATE_COURSE_CHOICE", "INVALID_RANKS"}


def test_required_course_cannot_be_ranked_as_elective():
    _, r = fixture()
    assert codes(check(requests=[replace(r, elective_choices=(CourseChoice("english", 1),))])) == {"DUPLICATE_COURSE_CHOICE"}


def test_duplicate_students_rejected():
    _, r = fixture()
    assert codes(check(requests=[r, r])) == {"DUPLICATE_STUDENT_REQUEST"}


def test_request_from_unrecognized_student_rejected():
    _, r = fixture()
    assert codes(check(requests=[replace(r, student_id="missing")])) == {"INVALID_STUDENT_SCOPE"}


def test_scope_required_and_input_limit_bounded():
    assert codes(check(school="")) == {"MISSING_SCOPE"}
    _, r = fixture()
    assert codes(check(requests=[r] * 5001)) == {"INPUT_LIMIT"}


def test_no_mutation_and_no_implicit_student_requirements():
    t, r = fixture()
    teachers, requests = {"t1": t}, [r]
    assert check(teachers=teachers, requests=requests) == ()
    assert teachers == {"t1": t} and requests == [r]
    assert check(teachers={}, requests=[]) == ()  # no complete-school claim made


def test_bool_or_float_elective_ranks_are_rejected():
    _, request = fixture()
    for rank in (True, 1.0, "1"):
        altered = replace(request, elective_choices=(CourseChoice("art", rank),))
        assert "INVALID_RANKS" in codes(check(requests=[altered]))


def test_noninteger_teacher_limits_and_truthy_identity_are_rejected():
    teacher, request = fixture()
    invalid = replace(teacher, max_instructional_minutes_per_cycle=True)
    assert "NEGATIVE_STAFF_LIMIT" in codes(check(teachers={"t1": invalid}))
    altered = replace(request, identity_verified=1)
    assert "STUDENT_IDENTITY_UNVERIFIED" in codes(check(requests=[altered]))


def test_large_duplicate_input_produces_bounded_error_output():
    _, request = fixture()
    result = check(requests=[request] * 1200)
    assert len(result) == MAX_REPORTED_FINDINGS + 1
    assert result[-1].code == "FINDINGS_TRUNCATED"
