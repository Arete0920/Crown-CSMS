"""
Controlled data-retention service.

All invocations are dry-run by default. Destructive execution requires an
explicit confirmation phrase, an approver identity, tenant scope (unless a
separate global override is supplied for an approved non-tenant model), a
positive retention window, bounded batches, cascade-free deletion, and an
audit row committed in the same transaction as the deletion.
"""
from __future__ import annotations

import logging
import secrets
import uuid
from contextlib import nullcontext
from datetime import timedelta
from typing import Any

from django.apps import apps
from django.conf import settings
from django.core.exceptions import FieldDoesNotExist
from django.db import transaction
from django.utils import timezone

from core.models_retention import DataRetentionPolicy, RetentionPurgeAudit

logger = logging.getLogger("crown.audit")

EXECUTION_CONFIRMATION = "PURGE_EXPIRED_RECORDS"
DEFAULT_BATCH_SIZE = 500
MAX_BATCH_SIZE = 1000
GLOBAL_MODEL_ALLOWLIST_SETTING = "CROWN_RETENTION_GLOBAL_MODEL_ALLOWLIST"
TENANT_FIELD_CANDIDATES = (
    "tenant_id",
    "school_id",
    "organization_id",
    "tenant",
    "school",
    "organization",
)


class RetentionAuthorizationError(ValueError):
    """Raised when destructive retention execution is not explicitly authorized."""


def _validate_execution(
    *, execute: bool, confirmation: str | None, approved_by: str | None
) -> None:
    if not isinstance(execute, bool):
        raise ValueError("execute must be a boolean")
    if not execute:
        return
    if not isinstance(confirmation, str) or not secrets.compare_digest(
        confirmation, EXECUTION_CONFIRMATION
    ):
        raise RetentionAuthorizationError(
            f"execution requires confirmation={EXECUTION_CONFIRMATION!r}"
        )
    if not isinstance(approved_by, str) or not approved_by.strip():
        raise RetentionAuthorizationError("execution requires a non-empty approved_by")


def _validate_batch_size(batch_size: int) -> int:
    if not isinstance(batch_size, int) or isinstance(batch_size, bool):
        raise ValueError("batch_size must be an integer")
    if batch_size < 1 or batch_size > MAX_BATCH_SIZE:
        raise ValueError(f"batch_size must be between 1 and {MAX_BATCH_SIZE}")
    return batch_size


def _validate_allow_global(allow_global: bool) -> bool:
    if not isinstance(allow_global, bool):
        raise ValueError("allow_global must be a boolean")
    return allow_global


def _normalize_tenant_id(tenant_id: Any) -> str | None:
    if tenant_id is None:
        return None
    normalized = str(tenant_id).strip()
    return normalized or None


def _approved_global_models() -> frozenset[str]:
    raw = getattr(settings, GLOBAL_MODEL_ALLOWLIST_SETTING, ())
    if isinstance(raw, str):
        values = raw.split(",")
    elif isinstance(raw, (list, tuple, set, frozenset)):
        values = raw
    else:
        raise ValueError(
            f"{GLOBAL_MODEL_ALLOWLIST_SETTING} must be a comma-separated string "
            "or an iterable of model labels"
        )
    return frozenset(
        str(value).strip().lower() for value in values if str(value).strip()
    )


def _valid_retention_days(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _has_created_at(model: Any) -> bool:
    meta = getattr(model, "_meta", None)
    if meta is None or not hasattr(meta, "get_field"):
        return hasattr(model, "created_at")
    try:
        meta.get_field("created_at")
    except (FieldDoesNotExist, LookupError):
        return False
    return True


def _tenant_field_name(model: Any) -> str | None:
    meta = getattr(model, "_meta", None)
    if meta is None or not hasattr(meta, "get_fields"):
        return None

    field_names = set()
    for field in meta.get_fields():
        name = getattr(field, "name", None)
        attname = getattr(field, "attname", None)
        if name:
            field_names.add(name)
        if attname:
            field_names.add(attname)

    for candidate in TENANT_FIELD_CANDIDATES:
        if candidate in field_names:
            if not candidate.endswith("_id") and f"{candidate}_id" in field_names:
                return f"{candidate}_id"
            return candidate
    return None


def _tenant_filter(
    model: Any, tenant_id: str | None
) -> tuple[dict[str, str], str | None]:
    tenant_field = _tenant_field_name(model)
    if tenant_id is None or tenant_field is None:
        return {}, tenant_field
    return {tenant_field: tenant_id}, tenant_field


def _primary_key_name(model: Any) -> str:
    meta = getattr(model, "_meta", None)
    pk = getattr(meta, "pk", None)
    return getattr(pk, "attname", None) or "pk"


def _model_label(model: Any, fallback: str) -> str:
    meta = getattr(model, "_meta", None)
    return getattr(meta, "label", None) or fallback


def _execution_transaction(policy: Any):
    """Use a real transaction for persisted policies and a no-op context for test doubles."""
    return transaction.atomic() if getattr(policy, "pk", None) is not None else nullcontext()


def _lock_policy_for_execution(policy: Any) -> Any:
    """Lock and refresh a persisted policy before destructive work begins."""
    policy_pk = getattr(policy, "pk", None)
    manager = getattr(DataRetentionPolicy, "objects", None)
    select_for_update = getattr(manager, "select_for_update", None)
    if policy_pk is None or not callable(select_for_update):
        return policy
    return select_for_update().get(pk=policy_pk)


def _record_audit(
    *,
    run_id: uuid.UUID,
    policy: Any,
    deleted_count: int,
    skipped_reason: str,
    snapshot: dict[str, Any],
) -> None:
    RetentionPurgeAudit.objects.create(
        run_id=run_id,
        model_name=policy.model_name,
        retention_days=policy.retention_days,
        legal_hold=policy.legal_hold,
        deleted_count=deleted_count,
        skipped_reason=skipped_reason,
        policy_snapshot=snapshot,
    )


def purge_expired_records(
    *,
    execute: bool = False,
    confirmation: str | None = None,
    approved_by: str | None = None,
    tenant_id: str | None = None,
    batch_size: int = DEFAULT_BATCH_SIZE,
    allow_global: bool = False,
) -> list[dict]:
    """Preview or execute retention policies with explicit safety controls.

    Dry-run is the default and never calls ``delete``. Destructive execution
    requires the exact confirmation phrase and an approver identity. Tenant
    scope is required for tenant-owned models. ``allow_global`` applies only
    to model labels present in ``CROWN_RETENTION_GLOBAL_MODEL_ALLOWLIST`` and
    only when the model has no recognized tenant field. Deletes are limited to
    ``batch_size`` primary records per query and roll back if cascades, policy
    changes, deletion errors, or audit-persistence errors are detected.
    """
    _validate_execution(
        execute=execute, confirmation=confirmation, approved_by=approved_by
    )
    batch_size = _validate_batch_size(batch_size)
    allow_global = _validate_allow_global(allow_global)
    tenant_id = _normalize_tenant_id(tenant_id)
    if execute and tenant_id is None and not allow_global:
        raise RetentionAuthorizationError(
            "execution requires a non-empty tenant_id or allow_global=True"
        )
    approved_global_models = _approved_global_models() if allow_global else frozenset()

    policies = DataRetentionPolicy.objects.all()
    results = []
    run_id = uuid.uuid4()
    dry_run = not execute
    mode = "dry_run" if dry_run else "execute"
    normalized_approver = approved_by.strip() if isinstance(approved_by, str) else None

    for policy in policies:
        result = {
            "model": policy.model_name,
            "mode": mode,
            "matched": 0,
            "selected": 0,
            "deleted": 0,
            "batches": 0,
            "tenant_field": None,
            "skipped_reason": None,
        }
        snapshot = {
            "model_name": policy.model_name,
            "retention_days": policy.retention_days,
            "legal_hold": policy.legal_hold,
            "mode": mode,
            "dry_run": dry_run,
            "approved_by": normalized_approver,
            "tenant_id": tenant_id,
            "tenant_field": None,
            "allow_global": allow_global,
            "global_model_approved": False,
            "batch_size": batch_size,
            "cutoff": None,
            "matched_count": 0,
            "selected_count": 0,
            "batch_count": 0,
            "primary_deleted_count": 0,
            "cascade_deleted_count": 0,
            "rolled_back": False,
        }

        if policy.legal_hold:
            result["skipped_reason"] = "legal hold enabled"
            _record_audit(
                run_id=run_id,
                policy=policy,
                deleted_count=0,
                skipped_reason=result["skipped_reason"],
                snapshot=snapshot,
            )
            results.append(result)
            logger.warning(
                "retention_purge: %s - skipped (legal hold enabled)",
                policy.model_name,
            )
            continue

        if not _valid_retention_days(policy.retention_days):
            result["skipped_reason"] = "invalid retention_days"
            _record_audit(
                run_id=run_id,
                policy=policy,
                deleted_count=0,
                skipped_reason=result["skipped_reason"],
                snapshot=snapshot,
            )
            results.append(result)
            logger.error(
                "retention_purge: %s - skipped (invalid retention_days=%r)",
                policy.model_name,
                policy.retention_days,
            )
            continue

        try:
            model = apps.get_model(policy.model_name)
        except (LookupError, ValueError) as exc:
            result["skipped_reason"] = f"model not found: {exc}"
            _record_audit(
                run_id=run_id,
                policy=policy,
                deleted_count=0,
                skipped_reason=result["skipped_reason"],
                snapshot=snapshot,
            )
            results.append(result)
            logger.warning("retention_purge: %s - %s", policy.model_name, exc)
            continue

        if not _has_created_at(model):
            result["skipped_reason"] = "no created_at field"
            _record_audit(
                run_id=run_id,
                policy=policy,
                deleted_count=0,
                skipped_reason=result["skipped_reason"],
                snapshot=snapshot,
            )
            results.append(result)
            continue

        tenant_filter, tenant_field = _tenant_filter(model, tenant_id)
        result["tenant_field"] = tenant_field
        snapshot["tenant_field"] = tenant_field

        if tenant_id is None:
            if tenant_field is not None or not allow_global:
                result["skipped_reason"] = "tenant scope required"
                _record_audit(
                    run_id=run_id,
                    policy=policy,
                    deleted_count=0,
                    skipped_reason=result["skipped_reason"],
                    snapshot=snapshot,
                )
                results.append(result)
                continue
            snapshot["global_model_approved"] = (
                policy.model_name.lower() in approved_global_models
            )
            if not snapshot["global_model_approved"]:
                result["skipped_reason"] = "global model not approved"
                _record_audit(
                    run_id=run_id,
                    policy=policy,
                    deleted_count=0,
                    skipped_reason=result["skipped_reason"],
                    snapshot=snapshot,
                )
                results.append(result)
                continue
        elif tenant_field is None:
            result["skipped_reason"] = "tenant field not found"
            _record_audit(
                run_id=run_id,
                policy=policy,
                deleted_count=0,
                skipped_reason=result["skipped_reason"],
                snapshot=snapshot,
            )
            results.append(result)
            continue

        if dry_run:
            cutoff = timezone.now() - timedelta(days=policy.retention_days)
            filters: dict[str, Any] = {"created_at__lt": cutoff, **tenant_filter}
            matched_count = model.objects.filter(**filters).count()
            result["matched"] = matched_count
            result["skipped_reason"] = "dry run"
            snapshot["matched_count"] = matched_count
            snapshot["cutoff"] = cutoff.isoformat()
            _record_audit(
                run_id=run_id,
                policy=policy,
                deleted_count=0,
                skipped_reason="dry run",
                snapshot=snapshot,
            )
            results.append(result)
            logger.info(
                "retention_purge: %s - dry run matched %d records",
                policy.model_name,
                matched_count,
            )
            continue

        pk_name = _primary_key_name(model)
        model_label = _model_label(model, policy.model_name)
        locked_policy = policy
        try:
            with _execution_transaction(policy):
                locked_policy = _lock_policy_for_execution(policy)
                snapshot["retention_days"] = locked_policy.retention_days
                snapshot["legal_hold"] = locked_policy.legal_hold
                if locked_policy.model_name != policy.model_name:
                    raise RuntimeError("retention policy model changed during execution")
                if locked_policy.legal_hold:
                    raise RuntimeError("legal hold enabled during execution")
                if not _valid_retention_days(locked_policy.retention_days):
                    raise RuntimeError("retention window became invalid during execution")

                cutoff = timezone.now() - timedelta(days=locked_policy.retention_days)
                filters = {"created_at__lt": cutoff, **tenant_filter}
                queryset = model.objects.filter(**filters)
                result["matched"] = queryset.count()
                snapshot["matched_count"] = result["matched"]
                snapshot["cutoff"] = cutoff.isoformat()

                while True:
                    batch_ids = list(
                        queryset.order_by(pk_name).values_list(pk_name, flat=True)[
                            :batch_size
                        ]
                    )
                    if not batch_ids:
                        break

                    result["selected"] += len(batch_ids)
                    snapshot["selected_count"] = result["selected"]
                    delete_filters = {**filters, f"{pk_name}__in": batch_ids}
                    deleted_total, deleted_by_model = model.objects.filter(
                        **delete_filters
                    ).delete()
                    primary_deleted = int(deleted_by_model.get(model_label, 0))
                    cascade_deleted = deleted_total - primary_deleted
                    snapshot["primary_deleted_count"] += primary_deleted
                    snapshot["cascade_deleted_count"] += cascade_deleted
                    if cascade_deleted:
                        raise RuntimeError(
                            "cascade deletion detected; use a model-specific purge path"
                        )
                    if primary_deleted < 1:
                        raise RuntimeError("batch delete made no progress")

                    result["deleted"] += primary_deleted
                    result["batches"] += 1
                    snapshot["batch_count"] = result["batches"]

                _record_audit(
                    run_id=run_id,
                    policy=locked_policy,
                    deleted_count=result["deleted"],
                    skipped_reason="",
                    snapshot=snapshot,
                )
        except Exception as exc:  # noqa: BLE001
            attempted_deleted = result["deleted"]
            attempted_batches = result["batches"]
            result["skipped_reason"] = f"execution rolled back: {exc}"
            result["deleted"] = 0
            result["batches"] = 0
            snapshot["attempted_primary_deleted_count"] = attempted_deleted
            snapshot["attempted_batch_count"] = attempted_batches
            snapshot["rolled_back"] = True
            try:
                _record_audit(
                    run_id=run_id,
                    policy=locked_policy,
                    deleted_count=0,
                    skipped_reason=result["skipped_reason"],
                    snapshot=snapshot,
                )
            except Exception as audit_exc:  # noqa: BLE001
                logger.exception(
                    "retention_purge: %s - execution rolled back but failure audit failed",
                    policy.model_name,
                )
                raise RuntimeError(
                    "retention execution rolled back and failure audit could not be written"
                ) from audit_exc
            logger.exception(
                "retention_purge: %s - execution rolled back after %d attempted batches",
                policy.model_name,
                attempted_batches,
            )
            raise

        logger.info(
            "retention_purge: %s - deleted %d primary records in %d batches",
            policy.model_name,
            result["deleted"],
            result["batches"],
        )
        results.append(result)

    return results
