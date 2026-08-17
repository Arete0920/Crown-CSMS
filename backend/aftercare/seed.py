from uuid import UUID

from .models import AftercareProgramConfig


def seed_aftercare_config(school_id: UUID) -> None:
    AftercareProgramConfig.objects.get_or_create(
        school_fk_id=school_id,
        defaults={
            "school_id": None,
            "late_fee_per_10_min": 10.00,
            "late_fee_grace_minutes": 0,
            "late_fee_cap": 100.00,
            "dropin_daily_rate": 15.00,
        },
    )
