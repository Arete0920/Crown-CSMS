from .models import AftercareProgramConfig


def seed_aftercare_config(school_id: int) -> None:
    AftercareProgramConfig.objects.get_or_create(
        school_id=school_id,
        defaults=dict(
            late_fee_per_10_min=10.00,
            late_fee_grace_minutes=0,
            late_fee_cap=100.00,
            dropin_daily_rate=15.00,
        ),
    )
