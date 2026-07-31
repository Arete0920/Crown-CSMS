from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass
from typing import Iterable

from django.contrib.auth import get_user_model

from households.models import Guardian


@dataclass(frozen=True)
class IdentityReconciliationRecord:
    guardian_id: str
    school_id: str
    household_id: str
    account_id: str | None
    email: str
    classification: str
    reason: str
    candidate_account_ids: tuple[str, ...] = ()
    canonical_guardian_id: str | None = None

    def as_dict(self) -> dict:
        payload = asdict(self)
        payload["candidate_account_ids"] = list(self.candidate_account_ids)
        return payload


def _normalized_email(value: str | None) -> str:
    return (value or "").strip().casefold()


def build_identity_reconciliation_report(*, school_id=None) -> dict:
    """Classify Parent360 identity records without mutating or inferring links."""

    user_model = get_user_model()
    guardian_qs = Guardian.objects.select_related("household", "account", "account__guardian").order_by(
        "school_id", "id"
    )
    account_qs = user_model.objects.select_related("guardian").order_by("school_id", "id")

    if school_id is not None:
        guardian_qs = guardian_qs.filter(school_id=school_id)
        account_qs = account_qs.filter(school_id=school_id)

    guardians = list(guardian_qs)
    accounts = list(account_qs)

    guardian_email_counts = Counter(
        (str(guardian.school_id), _normalized_email(guardian.email))
        for guardian in guardians
        if _normalized_email(guardian.email)
    )
    accounts_by_school_email: dict[tuple[str, str], list] = {}
    for account in accounts:
        email = _normalized_email(account.email)
        if not email or account.school_id is None:
            continue
        accounts_by_school_email.setdefault((str(account.school_id), email), []).append(account)

    records = [
        _classify_guardian(
            guardian,
            guardian_email_counts=guardian_email_counts,
            accounts_by_school_email=accounts_by_school_email,
        )
        for guardian in guardians
    ]
    summary = Counter(record.classification for record in records)

    return {
        "read_only": True,
        "automatic_linking": False,
        "school_id": str(school_id) if school_id is not None else None,
        "summary": dict(sorted(summary.items())),
        "total": len(records),
        "records": [record.as_dict() for record in records],
    }


def _classify_guardian(
    guardian: Guardian,
    *,
    guardian_email_counts: Counter,
    accounts_by_school_email: dict[tuple[str, str], list],
) -> IdentityReconciliationRecord:
    school_id = str(guardian.school_id)
    email = _normalized_email(guardian.email)
    base = {
        "guardian_id": str(guardian.id),
        "school_id": school_id,
        "household_id": str(guardian.household_id),
        "account_id": str(guardian.account_id) if guardian.account_id else None,
        "email": email,
    }

    if guardian.household.school_id != guardian.school_id:
        return IdentityReconciliationRecord(
            **base,
            classification="cross_tenant",
            reason="guardian_household_school_mismatch",
        )

    account = guardian.account if guardian.account_id else None
    if account is not None and account.school_id != guardian.school_id:
        return IdentityReconciliationRecord(
            **base,
            classification="cross_tenant",
            reason="guardian_account_school_mismatch",
            canonical_guardian_id=(
                str(account.guardian_id) if account.guardian_id else None
            ),
        )

    if not guardian.household.is_active:
        return IdentityReconciliationRecord(
            **base,
            classification="inactive_household",
            reason="linked_household_inactive",
        )

    if account is not None:
        if not account.is_active:
            return IdentityReconciliationRecord(
                **base,
                classification="inactive_account",
                reason="explicitly_linked_account_inactive",
                canonical_guardian_id=(
                    str(account.guardian_id) if account.guardian_id else None
                ),
            )
        if account.guardian_id:
            if account.guardian.school_id != guardian.school_id:
                return IdentityReconciliationRecord(
                    **base,
                    classification="canonical_identity_conflict",
                    reason="canonical_guardian_school_mismatch",
                    canonical_guardian_id=str(account.guardian_id),
                )
            return IdentityReconciliationRecord(
                **base,
                classification="manual_review",
                reason="dual_guardian_models_have_no_immutable_crosswalk",
                canonical_guardian_id=str(account.guardian_id),
            )
        return IdentityReconciliationRecord(
            **base,
            classification="mapped",
            reason="explicit_account_link_valid",
        )

    if not email:
        return IdentityReconciliationRecord(
            **base,
            classification="unmatched",
            reason="no_explicit_link_and_no_email_candidate_key",
        )

    if guardian_email_counts[(school_id, email)] > 1:
        return IdentityReconciliationRecord(
            **base,
            classification="duplicate_email",
            reason="multiple_compatibility_guardians_share_school_email",
        )

    candidates: Iterable = accounts_by_school_email.get((school_id, email), [])
    candidate_list = list(candidates)
    candidate_ids = tuple(str(account.id) for account in candidate_list)

    if not candidate_list:
        return IdentityReconciliationRecord(
            **base,
            classification="unmatched",
            reason="no_explicit_link_or_same_school_email_candidate",
        )
    if len(candidate_list) > 1:
        return IdentityReconciliationRecord(
            **base,
            classification="duplicate_email",
            reason="multiple_same_school_account_email_candidates",
            candidate_account_ids=candidate_ids,
        )

    candidate = candidate_list[0]
    if candidate.guardian_id and candidate.guardian.school_id != guardian.school_id:
        return IdentityReconciliationRecord(
            **base,
            classification="canonical_identity_conflict",
            reason="candidate_canonical_guardian_school_mismatch",
            candidate_account_ids=candidate_ids,
            canonical_guardian_id=str(candidate.guardian_id),
        )

    return IdentityReconciliationRecord(
        **base,
        classification="manual_review",
        reason=(
            "single_inactive_email_candidate_requires_review"
            if not candidate.is_active
            else "single_email_candidate_is_not_authorization"
        ),
        candidate_account_ids=candidate_ids,
        canonical_guardian_id=(str(candidate.guardian_id) if candidate.guardian_id else None),
    )
