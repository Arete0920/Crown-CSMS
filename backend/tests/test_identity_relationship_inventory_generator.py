import importlib.util
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
GENERATOR = REPO_ROOT / "tools" / "generate_identity_relationship_inventory.py"
EXPECTED_MODEL_SPECS = (
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


def load_generator():
    spec = importlib.util.spec_from_file_location("identity_relationship_inventory", GENERATOR)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_inventory_contract_is_metadata_only_and_deterministic():
    generator = load_generator()
    assert generator.DEFAULT_SETTINGS == "crown_api.settings"
    assert generator.MODEL_SPECS == EXPECTED_MODEL_SPECS
    source = GENERATOR.read_text(encoding="utf-8").lower()
    for token in (
        ".objects.", ".save(", ".delete(", ".update(", ".create(",
        "cursor.execute", "schema_editor", "subprocess", "requests.",
    ):
        assert token not in source


def test_extract_relationships_captures_declared_semantics():
    generator = load_generator()

    class TargetMeta:
        label = "core.Family"

    class Target:
        _meta = TargetMeta()

    def protect(*args, **kwargs):
        return None

    class Remote:
        model = Target
        on_delete = protect
        through = None
        related_name = "students"

    class Field:
        name = "family"
        is_relation = True
        auto_created = False
        one_to_one = False
        many_to_one = True
        many_to_many = False
        one_to_many = False
        null = False
        blank = False
        unique = False
        primary_key = False
        remote_field = Remote()

    class Meta:
        @staticmethod
        def get_fields():
            return [Field()]

    class Model:
        _meta = Meta()

    assert generator.extract_relationships(Model) == [{
        "field": "family",
        "relation_kind": "many_to_one",
        "target_model": "core.Family",
        "null": False,
        "blank": False,
        "unique": False,
        "primary_key": False,
        "on_delete": "protect",
        "through_model": None,
        "related_name": "students",
    }]


def test_relationship_sort_order_is_stable():
    generator = load_generator()

    class Remote:
        model = None
        on_delete = None
        through = None
        related_name = None

    class Field:
        is_relation = True
        auto_created = False
        one_to_one = False
        many_to_one = True
        many_to_many = False
        one_to_many = False
        null = False
        blank = False
        unique = False
        primary_key = False
        remote_field = Remote()

        def __init__(self, name):
            self.name = name

    class Meta:
        @staticmethod
        def get_fields():
            return [Field("zeta"), Field("alpha")]

    class Model:
        _meta = Meta()

    assert [item["field"] for item in generator.extract_relationships(Model)] == ["alpha", "zeta"]
