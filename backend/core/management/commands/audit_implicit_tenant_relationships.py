from __future__ import annotations

import hashlib
import json

from django.apps import apps
from django.core.exceptions import FieldDoesNotExist
from django.core.management import BaseCommand, CommandError
from django.db import models
from django.db.models import F


SUPPORTED_TENANT_FIELDS = ("school_id", "school", "tenant_id", "tenant")


def _manifest(ids: set[str], include_ids: bool) -> dict:
    ordered = sorted(ids)
    result = {
        "count": len(ordered),
        "sha256": hashlib.sha256("\n".join(ordered).encode("utf-8")).hexdigest(),
    }
    if include_ids:
        result["ids"] = ordered
    return result


def _row_ids(queryset) -> set[str]:
    return {str(pk) for pk in queryset.values_list("pk", flat=True).iterator()}


def _tenant_field(model: type[models.Model]) -> models.Field | None:
    for name in SUPPORTED_TENANT_FIELDS:
        try:
            field = model._meta.get_field(name)
        except FieldDoesNotExist:
            continue
        if name in {"school", "tenant"} and not isinstance(
            field, (models.ForeignKey, models.OneToOneField)
        ):
            continue
        return field
    return None


def _tenant_lookup(field: models.Field) -> str:
    return getattr(field, "attname", field.name)


def _tenant_anchor(field: models.Field) -> str:
    lookup = _tenant_lookup(field)
    return lookup[:-3] if lookup.endswith("_id") else field.name


def _tenant_type(field: models.Field) -> str:
    target = getattr(field, "target_field", None)
    return (target or field).get_internal_type()


def discover_relationships() -> list[tuple[type[models.Model], models.ManyToManyField]]:
    discovered: dict[tuple[str, str], tuple[type[models.Model], models.ManyToManyField]] = {}
    for owner_model in apps.get_models(include_auto_created=False):
        if not owner_model._meta.managed or _tenant_field(owner_model) is None:
            continue
        for field in owner_model._meta.local_many_to_many:
            if not isinstance(field, models.ManyToManyField):
                continue
            through_model = field.remote_field.through
            target_model = field.remote_field.model
            if not through_model._meta.auto_created:
                continue
            if not through_model._meta.managed or _tenant_field(target_model) is None:
                continue
            key = (owner_model._meta.label_lower, field.name)
            discovered[key] = (owner_model, field)
    return [discovered[key] for key in sorted(discovered)]


def reconcile_relationship(
    owner_model: type[models.Model],
    m2m_field: models.ManyToManyField,
    include_ids: bool,
) -> dict:
    through_model = m2m_field.remote_field.through
    target_model = m2m_field.remote_field.model
    owner_field_name = m2m_field.m2m_field_name()
    target_field_name = m2m_field.m2m_reverse_field_name()
    owner_field = through_model._meta.get_field(owner_field_name)
    target_field = through_model._meta.get_field(target_field_name)
    owner_tenant_field = _tenant_field(owner_model)
    target_tenant_field = _tenant_field(target_model)
    if owner_tenant_field is None or target_tenant_field is None:
        raise AssertionError("discovery returned a relationship without two tenant anchors")

    owner_tenant_lookup = _tenant_lookup(owner_tenant_field)
    target_tenant_lookup = _tenant_lookup(target_tenant_field)
    owner_anchor = _tenant_anchor(owner_tenant_field)
    target_anchor = _tenant_anchor(target_tenant_field)
    owner_type = _tenant_type(owner_tenant_field)
    target_type = _tenant_type(target_tenant_field)
    authority_verified = owner_anchor == target_anchor and owner_type == target_type

    queryset = through_model.objects.all()
    input_ids = _row_ids(queryset)
    dangling_owner_ids = _row_ids(
        queryset.exclude(
            **{
                f"{owner_field.attname}__in": owner_field.remote_field.model.objects.values(
                    owner_field.target_field.attname
                )
            }
        )
    )
    dangling_target_ids = _row_ids(
        queryset.exclude(
            **{
                f"{target_field.attname}__in": target_field.remote_field.model.objects.values(
                    target_field.target_field.attname
                )
            }
        )
    )
    dangling_ids = dangling_owner_ids | dangling_target_ids
    comparable = queryset.exclude(pk__in=dangling_ids)
    mismatch_ids = (
        _row_ids(
            comparable.exclude(
                **{
                    f"{owner_field_name}__{owner_tenant_lookup}": F(
                        f"{target_field_name}__{target_tenant_lookup}"
                    )
                }
            )
        )
        if authority_verified
        else set()
    )
    unresolved_authority_ids = set() if authority_verified else _row_ids(comparable)

    dangling_bucket = dangling_ids
    unresolved_bucket = unresolved_authority_ids - dangling_bucket
    mismatch_bucket = mismatch_ids - dangling_bucket - unresolved_bucket
    normal_bucket = input_ids - dangling_bucket - unresolved_bucket - mismatch_bucket
    accounted_ids = dangling_bucket | unresolved_bucket | mismatch_bucket | normal_bucket
    unexplained_ids = input_ids - accounted_ids
    buckets = (dangling_bucket, unresolved_bucket, mismatch_bucket, normal_bucket)
    overlap_count = sum(
        1 for row_id in input_ids if sum(row_id in bucket for bucket in buckets) != 1
    )

    return {
        "owner_model": owner_model._meta.label,
        "field": m2m_field.name,
        "target_model": target_model._meta.label,
        "through_model": through_model._meta.label,
        "owner_relation": owner_field_name,
        "target_relation": target_field_name,
        "owner_tenant_field": owner_tenant_lookup,
        "target_tenant_field": target_tenant_lookup,
        "owner_tenant_anchor": owner_anchor,
        "target_tenant_anchor": target_anchor,
        "owner_tenant_type": owner_type,
        "target_tenant_type": target_type,
        "tenant_authority_verified": authority_verified,
        "identity_partition": {
            "input": _manifest(input_ids, include_ids),
            "normal": _manifest(normal_bucket, include_ids),
            "dangling_endpoint": _manifest(dangling_bucket, include_ids),
            "unverified_authority": _manifest(unresolved_bucket, include_ids),
            "tenant_mismatch": _manifest(mismatch_bucket, include_ids),
            "unexplained": _manifest(unexplained_ids, include_ids),
            "accounted_unique_count": len(accounted_ids),
            "exclusive_overlap_count": overlap_count,
            "equation_holds": (
                input_ids == accounted_ids
                and not unexplained_ids
                and overlap_count == 0
            ),
        },
    }


def build_report(include_ids: bool = False) -> dict:
    discovered = discover_relationships()
    relationships = [
        reconcile_relationship(owner_model, field, include_ids)
        for owner_model, field in discovered
    ]
    mismatch_count = sum(
        row["identity_partition"]["tenant_mismatch"]["count"]
        for row in relationships
    )
    dangling_count = sum(
        row["identity_partition"]["dangling_endpoint"]["count"]
        for row in relationships
    )
    unverified_count = sum(
        row["identity_partition"]["unverified_authority"]["count"]
        for row in relationships
    )
    unexplained_count = sum(
        row["identity_partition"]["unexplained"]["count"]
        for row in relationships
    )
    equation_failure_count = sum(
        not row["identity_partition"]["equation_holds"] for row in relationships
    )
    return {
        "schema_version": 2,
        "mode": "read_only",
        "production_authorization": False,
        "totals": {
            "relationships": len(relationships),
            "tenant_mismatches": mismatch_count,
            "dangling_endpoints": dangling_count,
            "unverified_authority_rows": unverified_count,
            "unexplained": unexplained_count,
            "equation_failures": equation_failure_count,
        },
        "relationships": relationships,
    }


class Command(BaseCommand):
    help = "Reconcile tenant consistency for discovered implicit many-to-many through rows."

    def add_arguments(self, parser):
        parser.add_argument("--include-ids", action="store_true")
        parser.add_argument("--fail-on-anomaly", action="store_true")

    def handle(self, *args, **options):
        report = build_report(include_ids=options["include_ids"])
        self.stdout.write(json.dumps(report, indent=2, sort_keys=True))
        totals = report["totals"]
        anomaly_count = (
            totals["tenant_mismatches"]
            + totals["dangling_endpoints"]
            + totals["unverified_authority_rows"]
            + totals["unexplained"]
            + totals["equation_failures"]
        )
        if options["fail_on_anomaly"] and anomaly_count:
            raise CommandError(f"{anomaly_count} implicit tenant anomaly count(s)")
