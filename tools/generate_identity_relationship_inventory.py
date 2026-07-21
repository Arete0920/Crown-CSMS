from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SETTINGS = "crown_api.settings"
MODEL_SPECS = (
    ("canonical_core", "core", "Family"),
    ("canonical_core", "core", "Guardian"),
    ("canonical_core", "core", "Student"),
    ("households_compatibility", "households", "Household"),
    ("households_compatibility", "households", "Guardian"),
    ("households_compatibility", "households", "Student"),
    ("crown_api_compatibility", "crown_api", "Household"),
    ("crown_api_compatibility", "crown_api", "Person"),
    ("crown_api_compatibility", "crown_api", "HouseholdMember"),
    ("crown_api_compatibility", "crown_api", "Student"),
)


def configure_django(settings_module: str):
    os.environ["DJANGO_SETTINGS_MODULE"] = settings_module
    import django

    django.setup()
    from django.apps import apps

    return apps


def relation_kind(field) -> str:
    for attribute, label in (
        ("one_to_one", "one_to_one"),
        ("many_to_one", "many_to_one"),
        ("many_to_many", "many_to_many"),
        ("one_to_many", "one_to_many"),
    ):
        if getattr(field, attribute, False):
            return label
    return "relation"


def model_label(model) -> str | None:
    if model is None:
        return None
    if isinstance(model, str):
        return model
    meta = getattr(model, "_meta", None)
    return getattr(meta, "label", None)


def on_delete_name(field) -> str | None:
    remote = getattr(field, "remote_field", None)
    handler = getattr(remote, "on_delete", None)
    return getattr(handler, "__name__", None) if handler else None


def through_label(field) -> str | None:
    remote = getattr(field, "remote_field", None)
    through = getattr(remote, "through", None)
    return model_label(through)


def extract_relationships(model) -> list[dict]:
    relationships = []
    for field in model._meta.get_fields():
        if not getattr(field, "is_relation", False) or getattr(field, "auto_created", False):
            continue
        remote = getattr(field, "remote_field", None)
        target = model_label(getattr(remote, "model", None))
        relationships.append(
            {
                "field": field.name,
                "relation_kind": relation_kind(field),
                "target_model": target,
                "null": bool(getattr(field, "null", False)),
                "blank": bool(getattr(field, "blank", False)),
                "unique": bool(getattr(field, "unique", False)),
                "primary_key": bool(getattr(field, "primary_key", False)),
                "on_delete": on_delete_name(field),
                "through_model": through_label(field),
                "related_name": getattr(remote, "related_name", None),
            }
        )
    return sorted(relationships, key=lambda item: (item["field"], item["target_model"] or ""))


def build_inventory(settings_module: str = DEFAULT_SETTINGS) -> dict:
    apps = configure_django(settings_module)
    records = []
    failures = []

    for family, app_label, model_name in MODEL_SPECS:
        try:
            model = apps.get_model(app_label, model_name)
        except LookupError:
            failures.append(f"missing model: {app_label}.{model_name}")
            records.append({"family": family, "model": f"{app_label}.{model_name}", "table": None, "relationships": []})
            continue

        records.append({"family": family, "model": model._meta.label, "table": model._meta.db_table, "relationships": extract_relationships(model)})

    records.sort(key=lambda item: (item["family"], item["model"]))
    return {
        "schema_version": 1,
        "mode": "read_only_identity_relationship_metadata_inventory",
        "settings_module": settings_module,
        "database_queries_performed": False,
        "write_operations_permitted": False,
        "model_count": len(records),
        "relationship_count": sum(len(record["relationships"]) for record in records),
        "failures": sorted(failures),
        "records": records,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate declared identity-model relationship metadata.")
    parser.add_argument("--settings", default=DEFAULT_SETTINGS)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    inventory = build_inventory(args.settings)
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
