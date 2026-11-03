"""Audit the Heritage starter and optionally download the immutable source."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import runpy
import tempfile
import zipfile

from package_heritage_sales import ROOT, STARTER_FILES, pinned_revision


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
        if set(archive.namelist()) != {*STARTER_FILES, "HERITAGE-SALES-MANIFEST.json"}:
            raise RuntimeError("Unexpected ZIP entries.")
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
    except (OSError, RuntimeError, zipfile.BadZipFile, ValueError, KeyError) as exc:
        parser.exit(1, f"Heritage starter audit failed: {exc}\n")
