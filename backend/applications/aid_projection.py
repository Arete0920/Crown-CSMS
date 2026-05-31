from decimal import Decimal


def build_award_summary_by_household(*, school_id, household_ids):
    """
    Return a stable summary shape for admissions/parent continuity flows.

    This fallback keeps admissions endpoints bootable when award integrations are
    unavailable, while preserving the existing contract keys consumed by callers.
    """
    _ = school_id
    summaries = {}
    for household_id in household_ids or []:
        summaries[household_id] = {
            "count": 0,
            "total": str(Decimal("0")),
        }
    return summaries
