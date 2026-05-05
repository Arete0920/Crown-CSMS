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
import uuid

from django.apps import apps
from django.utils import timezone
from datetime import timedelta

from core.models_retention import DataRetentionPolicy, RetentionPurgeAudit

logger = logging.getLogger("crown.audit")


def purge_expired_records() -> list[dict]:
    """
    Iterate all active DataRetentionPolicy rows and delete expired records.

    Returns a list of result dicts: [{model, deleted, skipped_reason}]
    Legal-hold models and models without a created_at field are skipped.
    """
    policies = DataRetentionPolicy.objects.all()
    results = []
    run_id = uuid.uuid4()

    for policy in policies:
        result = {"model": policy.model_name, "deleted": 0, "skipped_reason": None}
        snapshot = {
            "model_name": policy.model_name,
            "retention_days": policy.retention_days,
            "legal_hold": policy.legal_hold,
        }

        if policy.legal_hold:
            result["skipped_reason"] = "legal hold enabled"
            results.append(result)
            logger.warning(
                "retention_purge: %s - skipped (legal hold enabled)", policy.model_name
            )
            RetentionPurgeAudit.objects.create(
                run_id=run_id,
                model_name=policy.model_name,
                retention_days=policy.retention_days,
                legal_hold=True,
                deleted_count=0,
                skipped_reason="legal hold enabled",
                policy_snapshot=snapshot,
            )
            continue

        try:
            model = apps.get_model(policy.model_name)
        except (LookupError, ValueError) as exc:
            result["skipped_reason"] = f"model not found: {exc}"
            results.append(result)
            logger.warning("retention_purge: %s — %s", policy.model_name, exc)
            RetentionPurgeAudit.objects.create(
                run_id=run_id,
                model_name=policy.model_name,
                retention_days=policy.retention_days,
                legal_hold=False,
                deleted_count=0,
                skipped_reason=result["skipped_reason"],
                policy_snapshot=snapshot,
            )
            continue

        if not hasattr(model, "created_at"):
            result["skipped_reason"] = "no created_at field"
            results.append(result)
            logger.info(
                "retention_purge: skipping %s (no created_at)", policy.model_name
            )
            RetentionPurgeAudit.objects.create(
                run_id=run_id,
                model_name=policy.model_name,
                retention_days=policy.retention_days,
                legal_hold=False,
                deleted_count=0,
                skipped_reason="no created_at field",
                policy_snapshot=snapshot,
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
            RetentionPurgeAudit.objects.create(
                run_id=run_id,
                model_name=policy.model_name,
                retention_days=policy.retention_days,
                legal_hold=False,
                deleted_count=deleted_count,
                skipped_reason="",
                policy_snapshot=snapshot,
            )
        except Exception as exc:  # noqa: BLE001
            result["skipped_reason"] = f"delete failed: {exc}"
            logger.error(
                "retention_purge: %s — delete failed: %s", policy.model_name, exc
            )
            RetentionPurgeAudit.objects.create(
                run_id=run_id,
                model_name=policy.model_name,
                retention_days=policy.retention_days,
                legal_hold=False,
                deleted_count=0,
                skipped_reason=result["skipped_reason"],
                policy_snapshot=snapshot,
            )

        results.append(result)

    return results
