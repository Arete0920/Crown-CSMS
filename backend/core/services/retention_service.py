"""
Data Retention Service.

Purges records that have exceeded their configured retention window.
Only models with a created_at field and an active DataRetentionPolicy are affected.
Models with legal_hold=True are always skipped.

Usage
-----
    from core.services.retention_service import purge_expired_records
    results = purge_expired_records()

Called by:
    python manage.py purge_expired_records
"""
import logging

from django.apps import apps
from django.utils import timezone
from datetime import timedelta

from core.models_retention import DataRetentionPolicy

logger = logging.getLogger("crown.audit")


def purge_expired_records() -> list[dict]:
    """
    Iterate all active DataRetentionPolicy rows and delete expired records.

    Returns a list of result dicts: [{model, deleted, skipped_reason}]
    Legal-hold models and models without a created_at field are skipped.
    """
    policies = DataRetentionPolicy.objects.filter(legal_hold=False)
    results = []

    for policy in policies:
        result = {"model": policy.model_name, "deleted": 0, "skipped_reason": None}

        try:
            model = apps.get_model(policy.model_name)
        except (LookupError, ValueError) as exc:
            result["skipped_reason"] = f"model not found: {exc}"
            results.append(result)
            logger.warning("retention_purge: %s — %s", policy.model_name, exc)
            continue

        if not hasattr(model, "created_at"):
            result["skipped_reason"] = "no created_at field"
            results.append(result)
            logger.info(
                "retention_purge: skipping %s (no created_at)", policy.model_name
            )
            continue

        cutoff = timezone.now() - timedelta(days=policy.retention_days)

        try:
            deleted_count, _ = model.objects.filter(created_at__lt=cutoff).delete()
            result["deleted"] = deleted_count
            logger.info(
                "retention_purge: %s — deleted %d records older than %s",
                policy.model_name,
                deleted_count,
                cutoff.date().isoformat(),
            )
        except Exception as exc:  # noqa: BLE001
            result["skipped_reason"] = f"delete failed: {exc}"
            logger.error(
                "retention_purge: %s — delete failed: %s", policy.model_name, exc
            )

        results.append(result)

    return results
