from __future__ import annotations

import json
from collections import Counter
from itertools import combinations

from django.apps import apps
from django.core.exceptions import FieldDoesNotExist
from django.core.management import BaseCommand, CommandError
from django.db import models

from core.management.commands.audit_tenant_relationship_integrity import RELATIONSHIPS


RELATION_FIELD_TYPES = (models.ForeignKey, models.OneToOneField)
TENANT_FIELD_CANDIDATES = ("school_id", "school", "tenant_id", "tenant")
TENANT_RELATION_NAMES = frozenset({"school", "tenant"})


def _concrete_field_type(field: models.Field) -> str:
    target_field = getattr(field, "target_field", None)
    if target_field is not None:
        return target_field.get_internal_type()
    return field.get_internal_type()


def _tenant_field(model) -> models.Field | None:
    for field_name in TENANT_FIELD_CANDIDATES:
        try:
            field = model._meta.get_field(field_name)
        except FieldDoesNotExist:
            continue
        if field_name in TENANT_RELATION_NAMES and not isinstance(
            field, RELATION_FIELD_TYPES
        ):
            continue
        return field
    return None


def _tenant_lookup(field: models.Field) -> str:
    return getattr(field, "attname", field.name)


def _tenant_anchor(field: models.Field) -> str:
    lookup = _tenant_lookup(field)
    if lookup.endswith("_id"):
        return lookup[:-3]
    return field.name


def _canonical_model_label(model_label: str) -> str:
    try:
        app_label, model_name = model_label.split(".", 1)
        return apps.get_model(app_label, model_name)._meta.label_lower
    except (LookupError, ValueError):
        return model_label.lower()


def _registered_relationship_keys() -> list[tuple[str, str, str]]:
    return [
        (_canonical_model_label(model_label), relation_name, parent_path)
        for model_label, parent_path, relation_name in RELATIONSHIPS
    ]


def _tenant_relations(model) -> list[tuple[models.Field, models.Field]]:
    relations = []
    for field in model._meta.get_fields():
        if not isinstance(field, RELATION_FIELD_TYPES) or not field.concrete:
            continue
        parent_tenant_field = _tenant_field(field.remote_field.model)
        if parent_tenant_field is not None:
            relations.append((field, parent_tenant_field))
    return relations


def _direct_relationships(model, tenant_field, registered):
    relationships = []
    model_label = model._meta.label
    model_key = model._meta.label_lower
    child_tenant_type = _concrete_field_type(tenant_field)
    child_tenant_anchor = _tenant_anchor(tenant_field)

    for field, parent_tenant_field in _tenant_relations(model):
        parent_lookup = _tenant_lookup(parent_tenant_field)
        parent_path = f"{field.name}__{parent_lookup}"
        registry_key = (model_key, field.name, parent_path)
        parent_tenant_type = _concrete_field_type(parent_tenant_field)
        parent_tenant_anchor = _tenant_anchor(parent_tenant_field)
        relationships.append(
            {
                "child_model": model_label,
                "child_model_key": model_key,
                "relation": field.name,
                "parent_model": field.remote_field.model._meta.label,
                "parent_tenant_path": parent_path,
                "relation_nullable": bool(field.null),
                "on_delete": getattr(
                    field.remote_field.on_delete,
                    "__name__",
                    str(field.remote_field.on_delete),
                ),
                "child_tenant_anchor": child_tenant_anchor,
                "parent_tenant_anchor": parent_tenant_anchor,
                "tenant_anchor_match": child_tenant_anchor == parent_tenant_anchor,
                "child_tenant_type": child_tenant_type,
                "parent_tenant_type": parent_tenant_type,
                "tenant_type_match": child_tenant_type == parent_tenant_type,
                "implicit_through": False,
                "registered": registry_key in registered,
            }
        )
    return relationships


def _implicit_through_relationships(model, registered):
    tenant_relations = _tenant_relations(model)
    relationships = []
    model_label = model._meta.label
    model_key = model._meta.label_lower

    for (left_field, left_tenant), (right_field, right_tenant) in combinations(
        tenant_relations, 2
    ):
        left_lookup = _tenant_lookup(left_tenant)
        right_lookup = _tenant_lookup(right_tenant)
        relation_name = left_field.name
        parent_path = f"{right_field.name}__{right_lookup}"
        registry_key = (model_key, relation_name, parent_path)
        left_type = _concrete_field_type(left_tenant)
        right_type = _concrete_field_type(right_tenant)
        left_anchor = _tenant_anchor(left_tenant)
        right_anchor = _tenant_anchor(right_tenant)
        relationships.append(
            {
                "child_model": model_label,
                "child_model_key": model_key,
                "relation": relation_name,
                "child_tenant_path": f"{left_field.name}__{left_lookup}",
                "parent_model": right_field.remote_field.model._meta.label,
                "parent_tenant_path": parent_path,
                "relation_nullable": bool(left_field.null or right_field.null),
                "on_delete": "implicit-through",
                "child_tenant_anchor": left_anchor,
                "parent_tenant_anchor": right_anchor,
                "tenant_anchor_match": left_anchor == right_anchor,
                "child_tenant_type": left_type,
                "parent_tenant_type": right_type,
                "tenant_type_match": left_type == right_type,
                "implicit_through": True,
                "registered": registry_key in registered,
            }
        )
    return relationships


def discover_tenant_models() -> list[dict]:
    registered = set(_registered_relationship_keys())
    rows: list[dict] = []

    for model in sorted(
        apps.get_models(include_auto_created=True),
        key=lambda item: item._meta.label_lower,
    ):
        options = model._meta
        if options.abstract or options.proxy or not options.managed:
            continue

        tenant_field = _tenant_field(model)
        if tenant_field is not None:
            relationships = _direct_relationships(model, tenant_field, registered)
            tenant_field_name = tenant_field.name
            tenant_attname = _tenant_lookup(tenant_field)
            tenant_anchor = _tenant_anchor(tenant_field)
            tenant_type = _concrete_field_type(tenant_field)
            tenant_scope_source = "direct"
        elif options.auto_created:
            relationships = _implicit_through_relationships(model, registered)
            if not relationships:
                continue
            tenant_field_name = None
            tenant_attname = None
            tenant_anchor = "derived"
            tenant_type = "derived"
            tenant_scope_source = "implicit-through-endpoints"
        else:
            continue

        relationships.sort(
            key=lambda item: (
                item["relation"],
                item["parent_model"],
                item["parent_tenant_path"],
            )
        )
        rows.append(
            {
                "model": options.label,
                "model_key": options.label_lower,
                "table": options.db_table,
                "auto_created": bool(options.auto_created),
                "tenant_scope_source": tenant_scope_source,
                "tenant_field": tenant_field_name,
                "tenant_attname": tenant_attname,
                "tenant_anchor": tenant_anchor,
                "tenant_type": tenant_type,
                "relationship_count": len(relationships),
                "relationships": relationships,
            }
        )

    return rows


def build_registry_report(models_inventory: list[dict]) -> dict:
    relationships = [
        relationship
        for model_row in models_inventory
        for relationship in model_row["relationships"]
    ]
    discovered_keys = {
        (
            relationship["child_model_key"],
            relationship["relation"],
            relationship["parent_tenant_path"],
        )
        for relationship in relationships
    }
    registered_keys = _registered_relationship_keys()
    registered_key_set = set(registered_keys)
    registered_counts = Counter(registered_keys)

    unregistered = [
        relationship for relationship in relationships if not relationship["registered"]
    ]
    type_mismatches = [
        relationship
        for relationship in relationships
        if not relationship["tenant_type_match"]
    ]
    anchor_mismatches = [
        relationship
        for relationship in relationships
        if not relationship["tenant_anchor_match"]
    ]
    stale_registered = [
        {
            "child_model": model_label,
            "relation": relation_name,
            "parent_tenant_path": parent_path,
        }
        for model_label, relation_name, parent_path in sorted(
            registered_key_set - discovered_keys
        )
    ]
    duplicate_registered = [
        {
            "child_model": model_label,
            "relation": relation_name,
            "parent_tenant_path": parent_path,
            "count": count,
        }
        for (model_label, relation_name, parent_path), count in sorted(
            registered_counts.items()
        )
        if count > 1
    ]
    tenant_types = Counter(
        model_row["tenant_type"] for model_row in models_inventory
    )
    tenant_anchors = Counter(
        model_row["tenant_anchor"] for model_row in models_inventory
    )

    return {
        "schema_version": 4,
        "mode": "read_only",
        "production_authorization": False,
        "totals": {
            "tenant_models": len(models_inventory),
            "tenant_relationships": len(relationships),
            "implicit_through_relationships": sum(
                1 for relationship in relationships if relationship["implicit_through"]
            ),
            "registered_relationships": len(relationships) - len(unregistered),
            "unregistered_relationships": len(unregistered),
            "stale_registered_relationships": len(stale_registered),
            "duplicate_registered_relationships": len(duplicate_registered),
            "tenant_type_mismatches": len(type_mismatches),
            "tenant_anchor_mismatches": len(anchor_mismatches),
        },
        "tenant_field_types": dict(sorted(tenant_types.items())),
        "tenant_anchors": dict(sorted(tenant_anchors.items())),
        "unregistered_relationships": unregistered,
        "stale_registered_relationships": stale_registered,
        "duplicate_registered_relationships": duplicate_registered,
        "tenant_type_mismatches": type_mismatches,
        "tenant_anchor_mismatches": anchor_mismatches,
        "models": models_inventory,
    }


class Command(BaseCommand):
    help = (
        "Read-only inventory of managed tenant-scoped models and "
        "tenant-owned parent relationships."
    )

    def add_arguments(self, parser):
        parser.add_argument("--fail-on-unregistered", action="store_true")
        parser.add_argument("--fail-on-stale-registry", action="store_true")
        parser.add_argument("--fail-on-type-mismatch", action="store_true")
        parser.add_argument("--fail-on-anchor-mismatch", action="store_true")
        parser.add_argument("--fail-on-incomplete", action="store_true")

    def handle(self, *args, **options):
        report = build_registry_report(discover_tenant_models())
        self.stdout.write(json.dumps(report, indent=2, sort_keys=True, default=str))

        totals = report["totals"]
        failures = []
        if options.get("fail_on_unregistered") and totals["unregistered_relationships"]:
            failures.append(
                f"{totals['unregistered_relationships']} unregistered relationship(s)"
            )
        if options.get("fail_on_stale_registry") and totals["stale_registered_relationships"]:
            failures.append(
                f"{totals['stale_registered_relationships']} stale registered relationship(s)"
            )
        if options.get("fail_on_type_mismatch") and totals["tenant_type_mismatches"]:
            failures.append(
                f"{totals['tenant_type_mismatches']} tenant type mismatch(es)"
            )
        if options.get("fail_on_anchor_mismatch") and totals["tenant_anchor_mismatches"]:
            failures.append(
                f"{totals['tenant_anchor_mismatches']} tenant anchor mismatch(es)"
            )
        if options.get("fail_on_incomplete"):
            incomplete_total = (
                totals["unregistered_relationships"]
                + totals["stale_registered_relationships"]
                + totals["duplicate_registered_relationships"]
                + totals["tenant_type_mismatches"]
                + totals["tenant_anchor_mismatches"]
            )
            if incomplete_total:
                failures.append(f"{incomplete_total} total registry completeness defect(s)")

        if failures:
            raise CommandError(
                "Tenant model registry audit failed: " + "; ".join(failures) + "."
            )
