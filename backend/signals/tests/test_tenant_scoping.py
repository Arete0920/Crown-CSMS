import pytest
from django.utils import timezone
from signals.models import SignalEvent, StudentRiskSnapshot

pytestmark = pytest.mark.django_db


def test_signal_event_scoped_by_school_id():
    SignalEvent.objects.create(
        school_id=1, student_id=1001, signal_key="x", weight=10, summary="a", details={}
    )
    SignalEvent.objects.create(
        school_id=2, student_id=1001, signal_key="x", weight=10, summary="b", details={}
    )

    assert SignalEvent.objects.filter(school_id=1).count() == 1
    assert SignalEvent.objects.filter(school_id=2).count() == 1


def test_snapshot_unique_per_day():
    d = timezone.now().date()
    StudentRiskSnapshot.objects.create(
        school_id=1, student_id=1001, as_of_date=d,
        risk_score=10, risk_level="LOW", drivers=[]
    )
    with pytest.raises(Exception):
        StudentRiskSnapshot.objects.create(
            school_id=1, student_id=1001, as_of_date=d,
            risk_score=20, risk_level="MED", drivers=[]
        )


def test_cross_school_snapshots_independent():
    d = timezone.now().date()
    StudentRiskSnapshot.objects.create(
        school_id=1, student_id=2000, as_of_date=d,
        risk_score=50, risk_level="MED", drivers=[]
    )
    StudentRiskSnapshot.objects.create(
        school_id=2, student_id=2000, as_of_date=d,
        risk_score=80, risk_level="HIGH", drivers=[]
    )

    assert StudentRiskSnapshot.objects.filter(school_id=1, student_id=2000).first().risk_level == "MED"
    assert StudentRiskSnapshot.objects.filter(school_id=2, student_id=2000).first().risk_level == "HIGH"
