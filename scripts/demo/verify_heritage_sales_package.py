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

from package_heritage_sales import ROOT, STARTER_FILES, pinned_revision

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


def verify_source_git_blobs(downloaded_source: Path, sha: str) -> None:
    """Require critical extracted files to equal Git objects at the pin.

    CI must check out the repository with enough history for `git show`.
    This is a selected-file identity check, not a comprehensive binary audit.
    """
    for relative in SOURCE_BLOB_PATHS:
        expected = subprocess.run(
            ["git", "-C", str(ROOT), "show", f"{sha}:{relative}"],
            capture_output=True, check=True,
        ).stdout
        downloaded_file = downloaded_source / relative
        if (not downloaded_file.is_file()
                or hashlib.sha256(downloaded_file.read_bytes()).digest()
                != hashlib.sha256(expected).digest()):
            raise RuntimeError(f"Downloaded source blob mismatch at {relative}")


def verify(*, download: bool = False):
    sha = pinned_revision()
    distribution = ROOT / ".local-backups" / "heritage-sales"
    package = distribution / f"CROWN-Heritage-Sales-Demo-{sha[:12]}.zip"
    report = distribution / "heritage-starter-audit.json"
    report.unlink(missing_ok=True)  # A failed rerun must not leave stale PASS evidence.
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
                or manifest.get("production_certified") is not False):
            raise RuntimeError("ZIP manifest does not match the approved sandbox contract.")
        with tempfile.TemporaryDirectory(prefix="heritage-package-audit-") as temp:
            directory = Path(temp)
            archive.extractall(directory)  # Exact four-entry allowlist above.
            starter = runpy.run_path(str(directory / "Install-and-Start-Heritage.py"))
            if starter["SOURCE_SHA"] != sha or starter["SOURCE_URL"] != source_url:
                raise RuntimeError("Bundled installer and manifest disagree.")
            if starter["DESTINATION"].name != f"Heritage-{sha[:12]}":
                raise RuntimeError("Bundled installer destination does not match SHA.")
            if download:
                installed = starter["install_source"](
                    destination=directory / f"Heritage-{sha[:12]}"
                )
                if (installed / "HERITAGE_SOURCE_COMMIT.txt").read_text(encoding="utf-8").strip() != sha:
                    raise RuntimeError("Downloaded source marker does not match SHA.")
                if not (installed / "scripts/demo/start_heritage_local.py").is_file():
                    raise RuntimeError("Downloaded source does not contain the launcher.")
                verify_source_git_blobs(installed, sha)
                # Repeat installs must reuse the exact same immutable source.
                again = starter["install_source"](
                    destination=directory / f"Heritage-{sha[:12]}"
                )
                if again != installed:
                    raise RuntimeError("Repeat installer did not reuse the same source.")
                # An existing folder with the wrong identity must fail closed.
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
    }
    report.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(evidence, indent=2))
    return evidence


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--download", action="store_true")
    args = parser.parse_args()
    try:
        verify(download=args.download)
    except (OSError, RuntimeError, subprocess.CalledProcessError,
            zipfile.BadZipFile, ValueError, KeyError) as exc:
        parser.exit(1, f"Heritage starter audit failed: {exc}\n")
