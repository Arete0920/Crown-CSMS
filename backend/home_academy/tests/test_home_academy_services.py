import uuid
import pytest

from home_academy.models import HomeAcademyEnrollment, HomeAcademyProgram, Offering, OfferingEnrollment
from home_academy.services import evaluate_offering_eligibility, homeschool_seats_remaining

pytestmark = pytest.mark.django_db


def make_program(school_id=None):
    school_id = school_id or uuid.uuid4()
    return HomeAcademyProgram.objects.create(
        school_id=school_id,
        public_program_name="Heritage Home Academy",
        active_school_year="2026-2027",
    )


def make_affiliate(program, student_id=None, status="homeschool_affiliate", school_of_record_status="parent_is_record"):
    student_id = student_id or uuid.uuid4()
    return HomeAcademyEnrollment.objects.create(
        school_id=program.school_id,
        student_id=student_id,
        program=program,
        status=status,
        school_of_record_status=school_of_record_status,
    )


def test_sport_blocks_sports_only_affiliate_without_two_courses():
    program = make_program()
    make_affiliate(program, student_id=uuid.UUID("00000000-0000-0000-0000-000000001001"))
    sport = Offering.objects.create(
        school_id=program.school_id,
        program=program,
        offering_type="sport",
        title="Varsity Soccer",
        homeschool_seat_cap=4,
        total_capacity=18,
        reserved_full_time_seats=10,
        buffer_seats=1,
        requires_admin_approval=False,
        requires_coach_or_director_approval=False,
    )

    result = evaluate_offering_eligibility(
        school_id=program.school_id,
        student_id=uuid.UUID("00000000-0000-0000-0000-000000001001"),
        offering=sport,
        forms_complete=True,
        account_current=True,
    )

    assert result.eligible is False
    assert "Requires at least 2 approved academic course(s)." in result.failures


def test_sport_allows_affiliate_with_two_active_academic_courses():
    program = make_program()
    make_affiliate(program, student_id=uuid.UUID("00000000-0000-0000-0000-000000001002"))
    for title in ["Algebra II", "Biology"]:
        course = Offering.objects.create(
            school_id=program.school_id,
            program=program,
            offering_type="academic_course",
            title=title,
            school_year="2026-2027",
            term="fall",
            credit_bearing=True,
            requires_academic_anchor=False,
            homeschool_seat_cap=10,
            requires_admin_approval=False,
        )
        OfferingEnrollment.objects.create(
            school_id=program.school_id,
            student_id=uuid.UUID("00000000-0000-0000-0000-000000001002"),
            offering=course,
            status="active",
            payment_status="paid",
            form_status="complete",
        )
    sport = Offering.objects.create(
        school_id=program.school_id,
        program=program,
        offering_type="sport",
        title="Basketball",
        school_year="2026-2027",
        term="fall",
        homeschool_seat_cap=4,
        total_capacity=18,
        reserved_full_time_seats=10,
        buffer_seats=1,
        requires_admin_approval=False,
        requires_coach_or_director_approval=False,
    )

    result = evaluate_offering_eligibility(
        school_id=program.school_id,
        student_id=uuid.UUID("00000000-0000-0000-0000-000000001002"),
        offering=sport,
        forms_complete=True,
        account_current=True,
    )

    assert result.eligible is True
    assert result.failures == []


def test_drama_blocks_without_one_academic_anchor():
    program = make_program()
    make_affiliate(program, student_id=uuid.UUID("00000000-0000-0000-0000-000000001003"))
    drama = Offering.objects.create(
        school_id=program.school_id,
        program=program,
        offering_type="drama",
        title="Spring Musical",
        homeschool_seat_cap=8,
        total_capacity=40,
        reserved_full_time_seats=25,
        buffer_seats=2,
        requires_admin_approval=False,
    )

    result = evaluate_offering_eligibility(
        school_id=program.school_id,
        student_id=uuid.UUID("00000000-0000-0000-0000-000000001003"),
        offering=drama,
        forms_complete=True,
        account_current=True,
    )

    assert result.eligible is False
    assert "Requires at least 1 approved academic course(s)." in result.failures


def test_school_of_record_student_satisfies_sport_anchor():
    program = make_program()
    make_affiliate(
        program,
        student_id=uuid.UUID("00000000-0000-0000-0000-000000001004"),
        status="homeschool_school_of_record",
        school_of_record_status="school_is_record",
    )
    sport = Offering.objects.create(
        school_id=program.school_id,
        program=program,
        offering_type="sport",
        title="Cross Country",
        homeschool_seat_cap=4,
        total_capacity=18,
        reserved_full_time_seats=10,
        buffer_seats=1,
        requires_admin_approval=False,
        requires_coach_or_director_approval=False,
    )

    result = evaluate_offering_eligibility(
        school_id=program.school_id,
        student_id=uuid.UUID("00000000-0000-0000-0000-000000001004"),
        offering=sport,
        forms_complete=True,
        account_current=True,
    )

    assert result.eligible is True


def test_capacity_protects_full_time_reserved_and_buffer_seats():
    program = make_program()
    offering = Offering.objects.create(
        school_id=program.school_id,
        program=program,
        offering_type="academic_course",
        title="Chemistry",
        homeschool_seat_cap=10,
        total_capacity=24,
        reserved_full_time_seats=20,
        buffer_seats=2,
        requires_academic_anchor=False,
    )

    assert homeschool_seats_remaining(offering) == 2


def test_no_released_homeschool_seats_blocks_registration():
    program = make_program()
    make_affiliate(program, student_id=uuid.UUID("00000000-0000-0000-0000-000000001005"))
    offering = Offering.objects.create(
        school_id=program.school_id,
        program=program,
        offering_type="academic_course",
        title="Calculus",
        homeschool_seat_cap=0,
        total_capacity=24,
        reserved_full_time_seats=20,
        buffer_seats=2,
        requires_academic_anchor=False,
        requires_admin_approval=False,
    )

    result = evaluate_offering_eligibility(
        school_id=program.school_id,
        student_id=uuid.UUID("00000000-0000-0000-0000-000000001005"),
        offering=offering,
        forms_complete=True,
        account_current=True,
    )

    assert result.eligible is False
    assert "No homeschool affiliate seats are currently available." in result.failures
