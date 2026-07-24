import importlib.util
import uuid
from pathlib import Path

from django.urls import resolve

from academics.views import SectionViewSet


REPO_ROOT = Path(__file__).resolve().parents[2]
VERIFIER = REPO_ROOT / "tools" / "verify_url_surface.py"


def load_verifier():
    spec = importlib.util.spec_from_file_location("url_resolver_manifest", VERIFIER)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_resolver_manifest_is_deterministic_and_precedence_ordered():
    verifier = load_verifier()

    first = verifier.build_manifest()
    second = verifier.build_manifest()

    assert first == second
    assert first["schema_version"] == 1
    assert first["mode"] == "read_only_django_resolver_manifest"
    assert first["record_count"] == len(first["records"])
    assert [record["order"] for record in first["records"]] == list(
        range(first["record_count"])
    )
    assert all(record["pattern"] for record in first["records"])
    assert all(record["callback"] for record in first["records"])


def test_manifest_captures_mount_name_namespace_and_callback():
    verifier = load_verifier()
    records = verifier.build_manifest()["records"]

    roster_records = [
        record
        for record in records
        if record["qualified_name"] == "academics-sections-roster"
    ]

    assert len(roster_records) == 2  # canonical /api/v1/ and compatibility /api/
    assert {record["callback"] for record in roster_records} == {
        "academics.views.SectionViewSet"
    }
    assert {record["pattern"].split("academics/sections", 1)[0] for record in roster_records} == {
        "api/v1/",
        "api/",
    }


def test_uuid_roster_path_resolves_to_single_canonical_viewset_action():
    section_id = uuid.uuid4()
    path = f"/api/v1/academics/sections/{section_id}/roster/"

    match = resolve(path)

    assert match.func.cls is SectionViewSet
    assert match.url_name == "academics-sections-roster"
    assert match.route.endswith("academics/sections/<pk>/roster/")
    assert match.kwargs == {"pk": str(section_id)}

    verifier = load_verifier()
    probe = verifier.resolve_probe(path)
    assert probe["callback"] == "academics.views.SectionViewSet"
    assert probe["url_name"] == "academics-sections-roster"
    assert probe["kwargs"] == {"pk": str(section_id)}


def test_verifier_remains_read_only():
    source = VERIFIER.read_text(encoding="utf-8").lower()
    for token in ("unlink(", "rmtree", "update_file", "delete_file"):
        assert token not in source
