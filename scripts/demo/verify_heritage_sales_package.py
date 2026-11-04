"""Audit the Heritage starter and optionally download the immutable source."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import runpy
import subprocess
import tempfile
import zipfile

from package_heritage_sales import (ROOT, STARTER_FILES, pinned_revision, render_installer,
                                    archive_name, render_readme)

# Exact Git blobs, rather than a downloaded marker alone, bind core runtime
# bytes to the immutable revision advertised in the starter manifest.
SOURCE_BLOB_PATHS = (
    "scripts/demo/start_heritage_local.py",
    "backend/manage.py",
    "backend/requirements.txt",
    "backend/sandbox_demo/services.py",
    "backend/sandbox_demo/management/commands/five_module_demo_preflight.py",
    "backend/aftercare/daycare_api.py",
    "backend/summer_camp/models.py",
    "backend/jireh_sgo/read_only_api.py",
    "frontend/dashboards/package-lock.json",
    "frontend/dashboards/src/routes/router.jsx",
    "frontend/dashboards/src/pages/JirehSGODashboard.jsx",
)
FIVE_MODULE_SOURCE_BLOB_PATHS = (
    "frontend/dashboards/scripts/heritage-daycare-presenter.mjs",
    "backend/sandbox_demo/management/commands/seed_local_diadem_pickup.py",
    "frontend/dashboards/scripts/write-build-json.mjs",
    "backend/sandbox_demo/management/commands/seed_heritage_module_samples.py",
    "backend/crown_api/management/commands/seed_fictional_sgo_intake.py",
    "backend/jireh_sgo/family_intake_api.py",
    "backend/aid/family_demo_intake.py",
    "frontend/dashboards/tests/e2e/summer-camp-local-readback.spec.ts",
    "frontend/dashboards/tests/e2e/extended-care-local-custody.spec.ts",
    "frontend/dashboards/tests/e2e/jireh-sgo-local-intake.spec.ts",
    "frontend/dashboards/tests/e2e/sandbox-parent-financial-aid-submit.spec.ts",
)


def verify_source_git_blobs(
    downloaded_source: Path, sha: str, *, five_module_candidate: bool = False,
) -> None:
    """Require critical extracted files to equal Git objects at the pin.

    CI must check out the repository with enough history for `git show`.
    This is a selected-file identity check, not a comprehensive binary audit.
    """
    paths = SOURCE_BLOB_PATHS + (FIVE_MODULE_SOURCE_BLOB_PATHS if five_module_candidate else ())
    for relative in paths:
        expected = subprocess.run(
            ["git", "-C", str(ROOT), "show", f"{sha}:{relative}"],
            capture_output=True, check=True,
        ).stdout
        downloaded_file = downloaded_source / relative
        if (not downloaded_file.is_file()
                or hashlib.sha256(downloaded_file.read_bytes()).digest()
                != hashlib.sha256(expected).digest()):
            raise RuntimeError(f"Downloaded source blob mismatch at {relative}")


def verify(
    *, download: bool = False, source_sha: str | None = None,
    five_module_candidate: bool = False,
):
    distribution = ROOT / ".local-backups" / "heritage-sales"
    report = distribution / (
        "heritage-five-module-candidate-audit.json" if five_module_candidate
        else "heritage-starter-audit.json"
    )
    report.unlink(missing_ok=True)  # Invalidate before pin/template validation.
    if five_module_candidate and source_sha is None:
        raise RuntimeError("Five-module audit requires explicit tested-source SHA")
    sha = source_sha if source_sha is not None else pinned_revision()
    expected_installer = render_installer(sha, five_module_candidate=five_module_candidate)
    expected_readme = render_readme(sha, five_module_candidate=five_module_candidate)
    package = distribution / archive_name(sha, five_module_candidate=five_module_candidate)
    if not package.is_file():
        raise RuntimeError("Build the exact ZIP before auditing it.")
    with zipfile.ZipFile(package) as archive:
        if archive.testzip() is not None:
            raise RuntimeError("Starter ZIP failed CRC verification.")
        names = archive.namelist()
        if (len(names) != len(STARTER_FILES) + 1
                or set(names) != {*STARTER_FILES, "HERITAGE-SALES-MANIFEST.json"}):
            raise RuntimeError("Unexpected or duplicate ZIP entries.")
        manifest = json.loads(archive.read("HERITAGE-SALES-MANIFEST.json"))
        source_url = f"https://github.com/Arete0920/Crown-CSMS/archive/{sha}.zip"
        if (manifest.get("source_sha") != sha
                or manifest.get("source_url") != source_url
                or manifest.get("launch") != "Start-Heritage.cmd"
                or manifest.get("entry") != "http://localhost:4173/sandbox"
                or manifest.get("external_payments") is not False
                or manifest.get("production_certified") is not False
                or manifest.get("release_certified") is not False
                or manifest.get("five_module_candidate") is not five_module_candidate):
            raise RuntimeError("ZIP manifest does not match the approved sandbox contract.")
        # ZIP CRC and an internally consistent manifest do not establish
        # the integrity of runnable installer code. Compare EVERY starter file
        # with the checked-out source before calling runpy on any code.
        for name in STARTER_FILES:
            expected = (
                expected_installer if name == "Install-and-Start-Heritage.py" else
                expected_readme if name == "HERITAGE-LOCAL-DEMO-README.txt" else
                (ROOT / name).read_bytes()
            )
            if archive.read(name) != expected:
                raise RuntimeError(f"Bundled {name} differs from the reviewed source template.")
        # Execute the audited template only after full byte comparison, never
        # arbitrary installer code taken from the archive before verification.
        with tempfile.TemporaryDirectory(prefix="heritage-reviewed-installer-") as temp:
            installer = Path(temp) / "Install-and-Start-Heritage.py"
            installer.write_bytes(expected_installer)
            starter = runpy.run_path(str(installer))
            if starter["SOURCE_SHA"] != sha or starter["SOURCE_URL"] != source_url:
                raise RuntimeError("Bundled installer and manifest disagree.")
            if starter["FIVE_MODULE_LAUNCH"] is not five_module_candidate:
                raise RuntimeError("Bundled installer launch mode differs from manifest.")
            if starter["DESTINATION"].name != f"Heritage-{sha[:12]}":
                raise RuntimeError("Bundled installer destination does not match SHA.")
            if download:
                with tempfile.TemporaryDirectory(prefix="heritage-package-audit-") as src_temp:
                    directory = Path(src_temp)
                    installed = starter["install_source"](
                        destination=directory / f"Heritage-{sha[:12]}"
                    )
                    if (installed / "HERITAGE_SOURCE_COMMIT.txt").read_text(encoding="utf-8").strip() != sha:
                        raise RuntimeError("Downloaded source marker does not match SHA.")
                    if not (installed / "scripts/demo/start_heritage_local.py").is_file():
                        raise RuntimeError("Downloaded source does not contain the launcher.")
                    verify_source_git_blobs(installed, sha, five_module_candidate=five_module_candidate)
                    again = starter["install_source"](
                        destination=directory / f"Heritage-{sha[:12]}"
                    )
                    if again != installed:
                        raise RuntimeError("Repeat installer did not reuse the same source.")
                    marker = installed / "HERITAGE_SOURCE_COMMIT.txt"
                    marker.write_text("0" * 40 + "\\n", encoding="utf-8")
                    try:
                        starter["install_source"](destination=installed)
                    except RuntimeError:
                        pass
                    else:
                        raise RuntimeError("Installer reused a source folder with wrong identity.")
    evidence = {
        "source_sha": sha,
        "zip_crc": "PASS",
        "manifest_and_bundled_installer": "PASS",
        "downloaded_source_critical_git_blobs": "PASS" if download else "NOT_RUN",
        "downloaded_source_identity_and_reinstall": "PASS" if download else "NOT_RUN",
        "five_module_browser_acceptance": "NOT_RUN_BY_THIS_SCRIPT",
        "physical_laptop_acceptance": "NOT_RUN_BY_THIS_SCRIPT",
        "five_module_candidate": five_module_candidate,
        "release_certified": False,
    }
    report.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(evidence, indent=2))
    return evidence


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--download", action="store_true")
    parser.add_argument("--source-sha", help="Exact checkout SHA of source-stamped candidate")
    parser.add_argument("--five-module-candidate", action="store_true",
                        help="Audit a guarded five-module candidate; never marks certified")
    args = parser.parse_args()
    try:
        verify(download=args.download, source_sha=args.source_sha,
               five_module_candidate=args.five_module_candidate)
    except (OSError, RuntimeError, subprocess.CalledProcessError,
            zipfile.BadZipFile, ValueError, KeyError) as exc:
        parser.exit(1, f"Heritage starter audit failed: {exc}\n")
