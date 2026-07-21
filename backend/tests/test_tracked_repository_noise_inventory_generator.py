import importlib.util
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
GENERATOR = REPO_ROOT / "tools" / "generate_tracked_repository_noise_inventory.py"


def load_generator():
    spec = importlib.util.spec_from_file_location("tracked_repository_noise_inventory", GENERATOR)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_inventory_is_deterministic_sorted_and_non_destructive():
    generator = load_generator()
    first = generator.build_inventory(REPO_ROOT)
    second = generator.build_inventory(REPO_ROOT)

    assert first == second
    assert first["schema_version"] == 1
    assert first["mode"] == "read_only_tracked_repository_noise_inventory"
    assert first["deletion_performed"] is False
    assert first["deletion_authorized"] is False
    assert first["record_count"] == len(first["records"])
    assert [record["path"] for record in first["records"]] == sorted(
        record["path"] for record in first["records"]
    )
    assert all(record["deletion_authorized"] is False for record in first["records"])


def test_classifier_flags_high_confidence_noise_without_deleting():
    generator = load_generator()

    assert generator.classify(Path("tmp/example.tmp"), 1) == ["temporary_or_os_artifact"]
    assert generator.classify(Path(".idea/workspace.xml"), 1) == ["editor_or_cache_artifact"]
    assert generator.classify(Path("audit-artifacts/raw.log"), 2_000_000) == ["oversized_tracked_log"]
    assert generator.classify(
        Path("docs/release/evidence/live-pack/20260101/copy.txt"), 1
    ) == ["nested_evidence_copy_requires_dedup_review"]


def test_generator_has_no_mutation_calls():
    source = GENERATOR.read_text(encoding="utf-8").lower()
    for token in (
        "unlink(",
        "rmtree(",
        "remove(",
        "delete_file",
        "update_file",
        "write_text(",
    ):
        assert token not in source
