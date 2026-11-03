"""Contract for a minimal immutable Heritage Windows sales starter."""
import ast
from unittest.mock import patch

import pytest
import importlib.util
import json
from pathlib import Path
import runpy
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


def test_installer_download_url_and_destination_match_immutable_source_pin():
    packager = loader()
    installer = runpy.run_path(str(ROOT / "Install-and-Start-Heritage.py"))
    source_sha = packager.pinned_revision()
    assert installer["SOURCE_SHA"] == source_sha
    assert installer["SOURCE_URL"] == f"https://github.com/Arete0920/Crown-CSMS/archive/{source_sha}.zip"
    assert installer["DESTINATION"].name == f"Heritage-{source_sha[:12]}"


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
            assert manifest["source_url"] == f"https://github.com/Arete0920/Crown-CSMS/archive/{manifest['source_sha']}.zip"
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


def _audit_fixture(monkeypatch, tmp_path):
    """Build the real starter in a disposable output and redirect audit paths."""
    import importlib

    monkeypatch.syspath_prepend(str(ROOT / "scripts" / "demo"))
    auditor = importlib.import_module("verify_heritage_sales_package")
    packager = loader()
    for name in packager.STARTER_FILES:
        (tmp_path / name).write_bytes((ROOT / name).read_bytes())
    destination = tmp_path / ".local-backups" / "heritage-sales"
    archive = packager.build(destination)
    monkeypatch.setattr(auditor, "ROOT", tmp_path)
    return auditor, archive, destination


def test_sale_audit_accepts_unchanged_starter_without_executing_zip_entry(monkeypatch, tmp_path):
    auditor, archive, destination = _audit_fixture(monkeypatch, tmp_path)
    result = auditor.verify(download=False)
    assert result["source_sha"] == loader().pinned_revision()
    assert result["manifest_and_bundled_installer"] == "PASS"
    assert result["downloaded_source_identity_and_reinstall"] == "NOT_RUN"
    assert (destination / "heritage-starter-audit.json").is_file()
    assert archive.is_file()


@pytest.mark.parametrize("changed", [
    "Install-and-Start-Heritage.py",
    "Start-Heritage.cmd",
    "HERITAGE-LOCAL-DEMO-README.txt",
])
def test_sale_audit_rejects_swapped_executable_or_instructions_without_execution(
    monkeypatch, tmp_path, changed,
):
    auditor, archive, destination = _audit_fixture(monkeypatch, tmp_path)
    with zipfile.ZipFile(archive) as original:
        entries = [(x.filename, original.read(x.filename)) for x in original.infolist()]
    with zipfile.ZipFile(archive, "w") as altered:
        for name, content in entries:
            if name == changed:
                content += b"\n# untrusted substituted ZIP entry\n"
            altered.writestr(name, content)
    # The verification must reject a modified ZIP before executing an
    # installer extracted from that ZIP (or any installer at all).
    with patch.object(auditor.runpy, "run_path", side_effect=AssertionError("untrusted ZIP executed")) as run_path:
        with pytest.raises(RuntimeError, match="differs from the checked-out source"):
            auditor.verify(download=False)
        run_path.assert_not_called()
    assert not (destination / "heritage-starter-audit.json").exists()
