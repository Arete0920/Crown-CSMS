import pytest
from datetime import date, time, datetime
from django.utils import timezone
from aftercare.models import AftercareProgramConfig
from aftercare.services import compute_late_fee

pytestmark = pytest.mark.django_db


def aware(dt: datetime) -> datetime:
    return timezone.make_aware(dt)


def test_late_fee_single_block():
    """1 minute late → 1 block → $10"""
    cfg = AftercareProgramConfig.objects.create(
        school_id=91,
        end_time=time(18, 0),
        late_fee_per_10_min=10.00,
        late_fee_grace_minutes=0,
        late_fee_cap=100.00,
    )
    d = date(2026, 2, 28)
    res = compute_late_fee(cfg, d, aware(datetime(2026, 2, 28, 18, 1)))
    assert res.late_minutes == 1
    assert res.late_fee_cents == 1000


def test_late_fee_10_min_boundary():
    """Exactly 10 min late → 1 block → $10"""
    cfg = AftercareProgramConfig.objects.create(
        school_id=92,
        end_time=time(18, 0),
        late_fee_per_10_min=10.00,
        late_fee_grace_minutes=0,
        late_fee_cap=100.00,
    )
    d = date(2026, 2, 28)
    res = compute_late_fee(cfg, d, aware(datetime(2026, 2, 28, 18, 10)))
    assert res.late_fee_cents == 1000


def test_late_fee_11_min_two_blocks():
    """11 min late → 2 blocks → $20"""
    cfg = AftercareProgramConfig.objects.create(
        school_id=93,
        end_time=time(18, 0),
        late_fee_per_10_min=10.00,
        late_fee_grace_minutes=0,
        late_fee_cap=100.00,
    )
    d = date(2026, 2, 28)
    res = compute_late_fee(cfg, d, aware(datetime(2026, 2, 28, 18, 11)))
    assert res.late_fee_cents == 2000


def test_late_fee_grace_absorbs_early():
    """4 min late with 5-min grace → no charge"""
    cfg = AftercareProgramConfig.objects.create(
        school_id=94,
        end_time=time(18, 0),
        late_fee_per_10_min=10.00,
        late_fee_grace_minutes=5,
        late_fee_cap=100.00,
    )
    d = date(2026, 2, 28)
    res = compute_late_fee(cfg, d, aware(datetime(2026, 2, 28, 18, 4)))
    assert res.late_fee_cents == 0


def test_late_fee_grace_then_one_block():
    """6 min late with 5-min grace → 1 billable min → 1 block → $10"""
    cfg = AftercareProgramConfig.objects.create(
        school_id=95,
        end_time=time(18, 0),
        late_fee_per_10_min=10.00,
        late_fee_grace_minutes=5,
        late_fee_cap=100.00,
    )
    d = date(2026, 2, 28)
    res = compute_late_fee(cfg, d, aware(datetime(2026, 2, 28, 18, 6)))
    assert res.late_fee_cents == 1000


def test_late_fee_cap_enforced():
    """999 blocks never exceeds cap of $100"""
    cfg = AftercareProgramConfig.objects.create(
        school_id=96,
        end_time=time(18, 0),
        late_fee_per_10_min=10.00,
        late_fee_grace_minutes=0,
        late_fee_cap=100.00,
    )
    d = date(2026, 2, 28)
    # 200 min late → 20 blocks → $200 → capped at $100
    res = compute_late_fee(cfg, d, aware(datetime(2026, 2, 28, 21, 20)))
    assert res.late_fee_cents == 10000  # $100.00


def test_on_time_no_fee():
    """Checkout exactly at cutoff → no fee"""
    cfg = AftercareProgramConfig.objects.create(
        school_id=97,
        end_time=time(18, 0),
        late_fee_per_10_min=10.00,
        late_fee_grace_minutes=0,
        late_fee_cap=100.00,
    )
    d = date(2026, 2, 28)
    res = compute_late_fee(cfg, d, aware(datetime(2026, 2, 28, 18, 0)))
    assert res.late_minutes == 0
    assert res.late_fee_cents == 0
