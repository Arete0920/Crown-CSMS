import pytest
from django.utils import timezone
from core.models import School
from households.models import Household, Student
from signals.models import SignalEvent, StudentRiskSnapshot

pytestmark = pytest.mark.django_db


def _make_student(*, school_name: str, first_name: str, last_name: str) -> tuple[School, Student]:
    school = School.objects.create(name=school_name)
    household = Household.objects.create(school_id=school.id, name=f"{school_name} Household")
    student = Student.objects.create(
        school_id=school.id,
        household=household,
        first_name=first_name,
        last_name=last_name,
    )
    return school, student


def test_signal_event_scoped_by_school_id():
    school_1, student_1 = _make_student(school_name="Signals School A", first_name="Alice", last_name="A")
    school_2, student_2 = _make_student(school_name="Signals School B", first_name="Bob", last_name="B")

    SignalEvent.objects.create(
        school_id=school_1.id,
        student=student_1,
        signal_key="x",
        weight=10,
        summary="a",
        details={},
    )
    SignalEvent.objects.create(
        school_id=school_2.id,
        student=student_2,
        signal_key="x",
        weight=10,
        summary="b",
        details={},
    )

    assert SignalEvent.objects.filter(school_id=school_1.id).count() == 1
    assert SignalEvent.objects.filter(school_id=school_2.id).count() == 1


def test_snapshot_unique_per_day():
    school, student = _make_student(school_name="Signals School Unique", first_name="Cara", last_name="C")
    d = timezone.now().date()
    StudentRiskSnapshot.objects.create(
        school_id=school.id,
        student=student,
        as_of_date=d,
        risk_score=10, risk_level="LOW", drivers=[]
    )
    with pytest.raises(Exception):
        StudentRiskSnapshot.objects.create(
            school_id=school.id,
            student=student,
            as_of_date=d,
            risk_score=20, risk_level="MED", drivers=[]
        )


def test_cross_school_snapshots_independent():
    school_1, student_1 = _make_student(school_name="Signals School C", first_name="Dana", last_name="D")
    school_2, student_2 = _make_student(school_name="Signals School D", first_name="Eli", last_name="E")
    d = timezone.now().date()
    StudentRiskSnapshot.objects.create(
        school_id=school_1.id,
        student=student_1,
        as_of_date=d,
        risk_score=50, risk_level="MED", drivers=[]
    )
    StudentRiskSnapshot.objects.create(
        school_id=school_2.id,
        student=student_2,
        as_of_date=d,
        risk_score=80, risk_level="HIGH", drivers=[]
    )

    assert StudentRiskSnapshot.objects.filter(school_id=school_1.id, student=student_1).first().risk_level == "MED"
    assert StudentRiskSnapshot.objects.filter(school_id=school_2.id, student=student_2).first().risk_level == "HIGH"
