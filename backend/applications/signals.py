from __future__ import annotations

from django.db.models.signals import post_save
from django.dispatch import receiver

from households.models import Guardian

from .models import Applicant


def _split_name(value: str) -> tuple[str, str]:
    parts = [part for part in str(value or "").strip().split() if part]
    if not parts:
        return "", ""
    if len(parts) == 1:
        return parts[0], ""
    return parts[0], " ".join(parts[1:])


def sync_applicant_household_guardians(applicant: Applicant) -> None:
    """Materialize submitted guardian contacts on the canonical household.

    Admissions intake stores the guardian payload on Applicant.flags. Parent360
    and enrollment continuity operate on households.Guardian, so the household
    must receive those contacts as first-class records. Guardian.account is left
    unset deliberately: an email address alone is not authorization to bind an
    authenticated account.
    """
    flags = applicant.flags if isinstance(applicant.flags, dict) else {}
    guardians = flags.get("guardians")
    if not isinstance(guardians, list):
        return

    household = applicant.application.household
    for raw_guardian in guardians:
        if not isinstance(raw_guardian, dict):
            continue
        email = str(raw_guardian.get("email") or "").strip().lower()
        if not email:
            continue
        first_name, last_name = _split_name(raw_guardian.get("guardianName") or raw_guardian.get("name") or "")
        if not first_name:
            continue

        guardian = Guardian.objects.filter(
            school_id=applicant.school_id,
            household=household,
            email__iexact=email,
        ).first()
        values = {
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "phone": str(raw_guardian.get("phone") or "").strip(),
            "is_primary": bool(raw_guardian.get("isPrimary")),
        }
        if guardian is None:
            Guardian.objects.create(
                school_id=applicant.school_id,
                household=household,
                account=None,
                **values,
            )
            continue

        changed = False
        for field, value in values.items():
            if getattr(guardian, field) != value:
                setattr(guardian, field, value)
                changed = True
        if changed:
            guardian.save(update_fields=[*values.keys(), "updated_at"])


@receiver(post_save, sender=Applicant, dispatch_uid="applications.sync_applicant_household_guardians")
def _sync_applicant_household_guardians(sender, instance: Applicant, raw: bool = False, **kwargs) -> None:
    if raw:
        return
    sync_applicant_household_guardians(instance)
