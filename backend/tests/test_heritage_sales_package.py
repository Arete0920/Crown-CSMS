"""Contract for a minimal immutable Heritage Windows sales starter."""
import ast
from unittest.mock import patch

import pytest
import importlib.util
import json
import os
import subprocess
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
        with pytest.raises(RuntimeError, match="differs from the reviewed source template"):
            auditor.verify(download=False)
        run_path.assert_not_called()
    assert not (destination / "heritage-starter-audit.json").exists()

def test_source_stamped_candidate_keeps_legacy_starter_unmodified(monkeypatch, tmp_path):
    """A reviewed source SHA is supplied at packaging, not committed into itself."""
    packager = loader()
    candidate_sha = "a" * 40
    legacy_pin = packager.pinned_revision()
    assert candidate_sha != legacy_pin
    monkeypatch.setattr(packager, "require_exact_candidate_checkout",
                       lambda sha: None if sha == candidate_sha else pytest.fail("Unexpected source revision"))
    zip_path = packager.build(tmp_path, source_sha=candidate_sha, five_module_candidate=True)
    with zipfile.ZipFile(zip_path) as archive:
        manifest = json.loads(archive.read("HERITAGE-SALES-MANIFEST.json"))
        entry = archive.read("Install-and-Start-Heritage.py").decode("utf-8")
        assert manifest["source_sha"] == candidate_sha
        assert manifest["five_module_candidate"] is True
        assert manifest["release_certified"] is False
        assert manifest["production_certified"] is False
        assert f'SOURCE_SHA = "{candidate_sha}"' in entry
        assert "FIVE_MODULE_LAUNCH = True" in entry
        assert 'command.append("--five-module-demo")' in entry
    assert f'SOURCE_SHA = "{legacy_pin}"' in (ROOT / "Install-and-Start-Heritage.py").read_text()
    assert "FIVE_MODULE_LAUNCH = False" in (ROOT / "Install-and-Start-Heritage.py").read_text()

def test_source_stamped_candidate_requires_real_checkout_identity(monkeypatch, tmp_path):
    packager = loader()
    candidate_sha = "a" * 40
    from types import SimpleNamespace
    monkeypatch.setattr(
        packager.subprocess, "run",
        lambda *args, **kwargs: SimpleNamespace(stdout="b" * 40 + "\\n"),
    )
    with pytest.raises(RuntimeError, match="does not match checked-out Git HEAD"):
        packager.build(tmp_path, source_sha=candidate_sha, five_module_candidate=True)
    assert list(tmp_path.iterdir()) == []

def test_source_stamped_candidate_requires_explicit_sha(tmp_path):
    packager = loader()
    with pytest.raises(RuntimeError, match="explicit source SHA"):
        packager.build(tmp_path, five_module_candidate=True)
    with pytest.raises(RuntimeError, match="40-character source SHA"):
        packager.render_installer("not-a-source-sha", five_module_candidate=True)

def test_stamped_candidate_audit_rejects_modified_installer_before_execution(monkeypatch, tmp_path):
    """Fail closed on a forged candidate even when the manifest claims its SHA."""
    packager = loader()
    monkeypatch.setattr(packager, "require_exact_candidate_checkout", lambda sha: None)
    candidate_sha = "a" * 40
    auditor, archive, destination = _audit_fixture(monkeypatch, tmp_path)
    # _audit_fixture exercises the unchanged legacy ZIP contract. Build a separate
    # source-stamped archive into the same disposable output directory.
    archive = packager.build(destination, source_sha=candidate_sha, five_module_candidate=True)
    with zipfile.ZipFile(archive) as source:
        contents = [(info.filename, source.read(info.filename)) for info in source.infolist()]
    with zipfile.ZipFile(archive, "w") as rewritten:
        for filename, payload in contents:
            if filename == "Install-and-Start-Heritage.py":
                payload += b"\\n# forbidden post-stamp code substitution\\n"
            rewritten.writestr(filename, payload)
    with patch.object(auditor.runpy, "run_path", side_effect=AssertionError("tampered installer executed")) as runner:
        with pytest.raises(RuntimeError, match="differs from the reviewed source template"):
            auditor.verify(source_sha=candidate_sha, five_module_candidate=True)
        runner.assert_not_called()
    assert not (destination / "heritage-starter-audit.json").exists()

def test_source_stamped_candidate_audit_accepts_exact_reviewed_template(monkeypatch, tmp_path):
    packager = loader()
    monkeypatch.setattr(packager, "require_exact_candidate_checkout", lambda sha: None)
    candidate_sha = "a" * 40
    auditor, _legacy_archive, destination = _audit_fixture(monkeypatch, tmp_path)
    packager.build(destination, source_sha=candidate_sha, five_module_candidate=True)
    proof = auditor.verify(source_sha=candidate_sha, five_module_candidate=True)
    assert proof["source_sha"] == candidate_sha
    assert proof["five_module_candidate"] is True
    assert proof["release_certified"] is False
    assert proof["downloaded_source_critical_git_blobs"] == "NOT_RUN"
    assert proof["five_module_browser_acceptance"] == "NOT_RUN_BY_THIS_SCRIPT"

def test_source_stamped_candidate_rejects_dirty_tracked_checkout(monkeypatch, tmp_path):
    """Matching HEAD is insufficient when reviewed tracked files differ."""
    packager = loader()
    from types import SimpleNamespace
    candidate_sha = "a" * 40
    observed = []
    def fake_git_run(command, **kwargs):
        observed.append(command)
        if command[1:3] == ["rev-parse", "HEAD"]:
            return SimpleNamespace(stdout=candidate_sha + "\n")
        if command[1:3] == ["status", "--porcelain"]:
            return SimpleNamespace(stdout=" M Install-and-Start-Heritage.py\n")
        pytest.fail(f"Unexpected Git invocation: {command}")

    monkeypatch.setattr(packager.subprocess, "run", fake_git_run)
    with pytest.raises(RuntimeError, match="modified tracked files"):
        packager.build(tmp_path, source_sha=candidate_sha, five_module_candidate=True)
    assert len(observed) == 2
    assert list(tmp_path.iterdir()) == []

def test_source_override_cannot_silently_build_basic_demo(tmp_path):
    packager = loader()
    with pytest.raises(RuntimeError, match="explicit five-module candidate"):
        packager.build(tmp_path, source_sha="a" * 40)

def test_candidate_and_basic_archives_coexist_with_same_sha(monkeypatch, tmp_path):
    """An uncertified candidate cannot silently replace the legacy sales ZIP."""
    packager = loader()
    sha = packager.pinned_revision()
    monkeypatch.setattr(packager, "require_exact_candidate_checkout", lambda s: None)
    basic = packager.build(tmp_path)
    original_bytes = basic.read_bytes()
    candidate = packager.build(tmp_path, source_sha=sha, five_module_candidate=True)
    assert basic != candidate
    assert basic.is_file() and candidate.is_file()
    assert basic.read_bytes() == original_bytes
    assert "UNCERTIFIED" in candidate.name
    with zipfile.ZipFile(candidate) as archive:
        content = archive.read("HERITAGE-LOCAL-DEMO-README.txt").decode("utf-8")
        assert f"Exact source SHA: {sha}" in content
        assert "TEST CANDIDATE ONLY" in content
        assert "start_heritage_local.py --five-module-demo" in content
        assert "Unmerged Camp PR" not in content
        assert "FIVE_MODULE_LAUNCH = True" in archive.read("Install-and-Start-Heritage.py").decode("utf-8")
    with zipfile.ZipFile(basic) as archive:
        assert archive.read("HERITAGE-LOCAL-DEMO-README.txt") == (ROOT / "HERITAGE-LOCAL-DEMO-README.txt").read_bytes()

def test_windows_upload_is_bound_to_tested_source_instead_of_historical_basic_zip():
    """A passing browser run must never publish the old basic-demo archive."""
    import yaml
    steps = yaml.safe_load((ROOT / ".github/workflows/heritage-windows-rehearsal.yml").read_text())["jobs"]["windows-local-demo"]["steps"]
    build = next(step for step in steps if "package_heritage_sales.py" in step.get("run", ""))
    assert build.get("id") == "tested_package"
    commands = build["run"]
    assert "$checkoutSha = git rev-parse HEAD" in commands
    assert "$checkoutSha -ne $env:GITHUB_SHA" in commands
    assert "package_heritage_sales.py --source-sha $checkoutSha --five-module-candidate" in commands
    assert "verify_heritage_sales_package.py --source-sha $checkoutSha --five-module-candidate --download" in commands
    assert 'archive=.local-backups/heritage-sales/CROWN-Heritage-Five-Module-UNCERTIFIED-$($checkoutSha.Substring(0,12)).zip' in commands
    upload = next(step for step in steps if step.get("with", {}).get("name") == "heritage-windows-buyer-rehearsed-candidate")
    assert upload["if"] == "success()"
    assert upload["with"]["path"].splitlines() == [
        "${{ steps.tested_package.outputs.archive }}",
        ".local-backups/heritage-sales/heritage-five-module-candidate-audit.json",
    ]

@pytest.mark.parametrize("variables,expected", [
    ({"VITE_BUILD_SHA": "a" * 40, "GITHUB_SHA": "b" * 40}, "a" * 40),
    ({"BUILD_SHA": "a" * 40, "GITHUB_SHA": "b" * 40}, "a" * 40),
    ({"GITHUB_SHA": "a" * 40}, "a" * 40),
    ({"VITE_BUILD_SHA": "invalid", "GITHUB_SHA": "a" * 40}, None),
    ({}, None),
])
def test_gitless_frontend_build_identity(tmp_path, variables, expected):
    env = {k: v for k, v in os.environ.items() if k not in {"VITE_BUILD_SHA", "BUILD_SHA", "GITHUB_SHA", "GIT_DIR", "GIT_WORK_TREE"}}
    env.update(variables)
    result = subprocess.run(["node", str(ROOT / "frontend/dashboards/scripts/write-build-json.mjs")], cwd=tmp_path, env=env, capture_output=True, text=True)
    target = tmp_path / "dist/build.json"
    if expected:
        assert result.returncode == 0, result.stderr
        data = json.loads(target.read_text())
        assert (data["build_sha"], data["build_sha_short"]) == (expected, expected[:7])
    else:
        assert result.returncode != 0 and "Build provenance" in result.stderr
        assert not target.exists()
