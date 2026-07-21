from __future__ import annotations

import argparse
import json
import os
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SETTINGS = "crown_api.settings"
MODEL_SPECS = (
    ("canonical_core", "core", "Family", "school_id"),
    ("canonical_core", "core", "Guardian", "school_id"),
    ("canonical_core", "core", "Student", "school_id"),
    ("households_compatibility", "households", "Household", "school_id"),
    ("households_compatibility", "households", "Guardian", "school_id"),
    ("households_compatibility", "households", "Student", "school_id"),
    ("crown_api_compatibility", "crown_api", "Household", None),
    ("crown_api_compatibility", "crown_api", "Person", None),
    ("crown_api_compatibility", "crown_api", "HouseholdMember", None),
    ("crown_api_compatibility", "crown_api", "Student", None),
)


def configure_django(settings_module: str):
    os.environ["DJANGO_SETTINGS_MODULE"] = settings_module
    import django

    django.setup()
    from django.apps import apps
    from django.db import connections

    return apps, connections


def count_tenants(model, tenant_field: str | None, database: str = "default") -> dict:
    if not tenant_field:
        return {"tenant_scoped": False, "tenant_field": None, "tenant_counts": {}}
    field_names = {field.attname for field in model._meta.get_fields() if hasattr(field, "attname")}
    if tenant_field not in field_names:
        return {
            "tenant_scoped": False,
            "tenant_field": tenant_field,
            "tenant_counts": {},
            "error": "declared tenant field is missing",
        }
    manager = model._default_manager.using(database)
    values = manager.values_list(tenant_field, flat=True)
    counts = Counter("null" if value is None else str(value) for value in values)
    return {
        "tenant_scoped": True,
        "tenant_field": tenant_field,
        "tenant_counts": dict(sorted(counts.items())),
    }


def build_inventory(settings_module: str = DEFAULT_SETTINGS, database: str = "default") -> dict:
    apps, connections = configure_django(settings_module)
    connection = connections[database]
    table_names = set(connection.introspection.table_names())
    records = []
    failures = []

    for family, app_label, model_name, tenant_field in MODEL_SPECS:
        try:
            model = apps.get_model(app_label, model_name)
        except LookupError:
            failures.append(f"missing model: {app_label}.{model_name}")
            records.append(
                {
                    "family": family,
                    "app_label": app_label,
                    "model": model_name,
                    "table": None,
                    "table_present": False,
                    "row_count": None,
                    "tenant_scoped": False,
                    "tenant_field": tenant_field,
                    "tenant_counts": {},
                }
            )
            continue

        table = model._meta.db_table
        record = {
            "family": family,
            "app_label": app_label,
            "model": model_name,
            "table": table,
            "table_present": table in table_names,
            "row_count": None,
        }
        if table not in table_names:
            failures.append(f"missing table: {table}")
            record["tenant_scoped"] = False
            record["tenant_field"] = tenant_field
            record["tenant_counts"] = {}
        else:
            manager = model._default_manager.using(database)
            record["row_count"] = manager.count()
            tenant = count_tenants(model, tenant_field, database)
            record["tenant_scoped"] = tenant["tenant_scoped"]
            record["tenant_field"] = tenant["tenant_field"]
            record["tenant_counts"] = tenant["tenant_counts"]
            if tenant.get("error"):
                record["error"] = tenant["error"]
                failures.append(f"{app_label}.{model_name}: {tenant['error']}")
        records.append(record)

    records.sort(key=lambda item: (item["family"], item["app_label"], item["model"]))
    family_totals = Counter()
    for record in records:
        if record["row_count"] is not None:
            family_totals[record["family"]] += record["row_count"]

    return {
        "schema_version": 1,
        "mode": "read_only_database_inventory",
        "settings_module": settings_module,
        "database_alias": database,
        "write_operations_permitted": False,
        "record_count": len(records),
        "family_row_totals": dict(sorted(family_totals.items())),
        "failures": sorted(failures),
        "records": records,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate read-only identity row-count and tenant-distribution evidence.")
    parser.add_argument("--settings", default=DEFAULT_SETTINGS)
    parser.add_argument("--database", default="default")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    inventory = build_inventory(args.settings, args.database)
    rendered = json.dumps(inventory, indent=2, sort_keys=True) + "\n"
    if args.output:
        output = args.output if args.output.is_absolute() else REPO_ROOT / args.output
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 1 if inventory["failures"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
