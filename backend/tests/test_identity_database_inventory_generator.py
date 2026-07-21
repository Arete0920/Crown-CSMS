import importlib.util
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
GENERATOR = REPO_ROOT / "tools" / "generate_identity_database_inventory.py"
EXPECTED_MODEL_SPECS = (
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


def load_generator():
    spec = importlib.util.spec_from_file_location("identity_database_inventory", GENERATOR)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_inventory_contract_is_deterministic_and_read_only():
    generator = load_generator()

    assert generator.DEFAULT_SETTINGS == "crown_api.settings"
    assert generator.MODEL_SPECS == EXPECTED_MODEL_SPECS

    source = GENERATOR.read_text(encoding="utf-8").lower()
    forbidden = (
        ".save(",
        ".delete(",
        ".update(",
        ".create(",
        "bulk_create",
        "bulk_update",
        "transaction.atomic",
        "cursor.execute",
        "schema_editor",
    )
    for token in forbidden:
        assert token not in source


def test_inventory_declares_expected_identity_families_and_tenant_fields():
    generator = load_generator()
    specs = {(family, app, model): tenant for family, app, model, tenant in generator.MODEL_SPECS}

    assert specs[("canonical_core", "core", "Family")] == "school_id"
    assert specs[("canonical_core", "core", "Guardian")] == "school_id"
    assert specs[("canonical_core", "core", "Student")] == "school_id"
    assert specs[("households_compatibility", "households", "Household")] == "school_id"
    assert specs[("households_compatibility", "households", "Guardian")] == "school_id"
    assert specs[("households_compatibility", "households", "Student")] == "school_id"
    assert specs[("crown_api_compatibility", "crown_api", "Household")] is None
    assert specs[("crown_api_compatibility", "crown_api", "Person")] is None
    assert specs[("crown_api_compatibility", "crown_api", "HouseholdMember")] is None
    assert specs[("crown_api_compatibility", "crown_api", "Student")] is None


def test_count_tenants_marks_unscoped_models_without_querying():
    generator = load_generator()

    class Model:
        pass

    assert generator.count_tenants(Model, None, "reporting") == {
        "tenant_scoped": False,
        "tenant_field": None,
        "tenant_counts": {},
    }


def test_count_tenants_uses_requested_database_alias():
    generator = load_generator()
    calls = []

    class Field:
        attname = "school_id"

    class Meta:
        @staticmethod
        def get_fields():
            return [Field()]

    class Values:
        def __iter__(self):
            return iter(["tenant-b", "tenant-a", "tenant-b"])

    class Manager:
        def using(self, alias):
            calls.append(("using", alias))
            return self

        def values_list(self, field, flat=False):
            calls.append(("values_list", field, flat))
            return Values()

    class Model:
        _meta = Meta()
        _default_manager = Manager()

    assert generator.count_tenants(Model, "school_id", "reporting") == {
        "tenant_scoped": True,
        "tenant_field": "school_id",
        "tenant_counts": {"tenant-a": 1, "tenant-b": 2},
    }
    assert calls == [("using", "reporting"), ("values_list", "school_id", True)]
