"""Contract for a minimal immutable Heritage Windows sales starter."""
import ast
import importlib.util
import json
from pathlib import Path
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[2]


def loader():
    script = ROOT / "scripts/demo/package_heritage_sales.py"
    spec = importlib.util.spec_from_file_location("heritage_sales_packager", script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_starter_is_version_pinned_to_a_git_commit():
    p = ast.parse((ROOT / "Install-and-Start-Heritage.py").read_text(encoding="utf-8"))
    assert p
    packager = loader()
    assert len(packager.pinned_revision()) == 40


def test_starter_package_contains_no_database_secret_or_credential_file():
    packager = loader()
    with tempfile.TemporaryDirectory() as d:
        output = packager.build(Path(d))
        with zipfile.ZipFile(output) as archive:
            names = set(archive.namelist())
            assert names == {*packager.STARTER_FILES, "HERITAGE-SALES-MANIFEST.json"}
            assert archive.testzip() is None
            manifest = json.loads(archive.read("HERITAGE-SALES-MANIFEST.json"))
            assert manifest["source_sha"] == packager.pinned_revision()
            assert manifest["external_payments"] is False
            assert manifest["production_certified"] is False
            assert "Crown-CSMS" in archive.read("Install-and-Start-Heritage.py").decode("utf-8")
            assert not any("password" in item.lower() or item.endswith(".sqlite3") for item in names)


def test_starter_rejects_cross_repo_and_archive_traversal():
    source = (ROOT / "Install-and-Start-Heritage.py").read_text(encoding="utf-8")
    assert "target.is_relative_to(unpack.resolve())" in source
    assert "member.external_attr" in source
    assert "Arete0920/Crown-CSMS" in source
    assert 'HERITAGE_SOURCE_COMMIT.txt' in source
