"""Build an auditable, minimal Windows starter for the approved Heritage local demo.

The ZIP intentionally excludes application source, secrets, databases and dependencies.
The first launch downloads an immutable commit from the authoritative public repository.
"""
from __future__ import annotations

import ast
import json
from pathlib import Path
import re
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[2]
STARTER_FILES = (
    "Start-Heritage.cmd",
    "Install-and-Start-Heritage.py",
    "HERITAGE-LOCAL-DEMO-README.txt",
)


def pinned_revision() -> str:
    installer = ast.parse((ROOT / "Install-and-Start-Heritage.py").read_text(encoding="utf-8"))
    for node in installer.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "SOURCE_SHA" for t in node.targets):
            sha = ast.literal_eval(node.value)
            if isinstance(sha, str) and re.fullmatch(r"[0-9a-f]{40}", sha):
                return sha
    raise RuntimeError("Heritage installer is not pinned to a valid 40-character Git revision")

def render_installer(source_sha: str, *, five_module_candidate: bool = False) -> bytes:
    """Stamp only two reviewed literal fields; never edit the repository source.

    A Git commit cannot embed its own 40-character SHA without changing the
    commit identity. The distributable therefore gets its tested source pin
    at package-build time, not through a source commit that claims itself.
    """
    if not isinstance(source_sha, str) or not re.fullmatch(r"[0-9a-f]{40}", source_sha):
        raise RuntimeError("Release candidate needs one exact 40-character source SHA")
    template = (ROOT / "Install-and-Start-Heritage.py").read_text(encoding="utf-8")
    old_pin = pinned_revision()
    expected = f'SOURCE_SHA = "{old_pin}"'
    if template.count(expected) != 1 or template.count("FIVE_MODULE_LAUNCH = False") != 1:
        raise RuntimeError("Reviewed starter template is not the expected version")
    rendered = template.replace(expected, f'SOURCE_SHA = "{source_sha}"', 1)
    rendered = rendered.replace(
        "FIVE_MODULE_LAUNCH = False",
        "FIVE_MODULE_LAUNCH = True" if five_module_candidate else "FIVE_MODULE_LAUNCH = False",
        1,
    )
    return rendered.encode("utf-8")


def require_exact_candidate_checkout(source_sha: str) -> None:
    """Do not stamp one Git revision into a package built from another."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True,
            check=True, text=True, timeout=15,
        )
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        raise RuntimeError("Cannot establish exact Git checkout for candidate packaging") from exc
    if result.stdout.strip() != source_sha:
        raise RuntimeError("Candidate package source SHA does not match checked-out Git HEAD")
    try:
        tracked = subprocess.run(
            ["git", "status", "--porcelain", "--untracked-files=no"],
            cwd=ROOT, capture_output=True, check=True, text=True, timeout=15,
        )
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        raise RuntimeError("Cannot verify clean tracked Git checkout for candidate packaging") from exc
    if tracked.stdout.strip():
        raise RuntimeError("Candidate package checkout has modified tracked files")


def archive_name(source_sha: str, *, five_module_candidate: bool = False) -> str:
    """Use distinct filenames so an uncertified candidate cannot replace a basic ZIP."""
    if five_module_candidate:
        return f"CROWN-Heritage-Five-Module-UNCERTIFIED-{source_sha[:12]}.zip"
    return f"CROWN-Heritage-Sales-Demo-{source_sha[:12]}.zip"


def render_readme(source_sha: str, *, five_module_candidate: bool = False) -> bytes:
    """Do not redistribute the outdated basic-demo README with a five-module pin."""
    if not five_module_candidate:
        return (ROOT / "HERITAGE-LOCAL-DEMO-README.txt").read_bytes()
    return (
        "CROWN HERITAGE FIVE-MODULE LOCAL DEMO - UNCERTIFIED CANDIDATE\n"
        f"Exact source SHA: {source_sha}\n"
        "\n"
        "This ZIP is a TEST CANDIDATE ONLY. It does not certify browser journeys,\n"
        "the downloaded build, an SGO partnership, Azure, payments or physical laptops.\n"
        "\n"
        "1. On Windows install Python 3.12 and Node.js 24 with npm.\n"
        "2. Extract the ZIP into a writable folder; run Start-Heritage.cmd.\n"
        "3. The installer downloads the immutable source SHA above, then invokes\n"
        "   scripts/demo/start_heritage_local.py --five-module-demo explicitly.\n"
        "4. The launcher fails closed if required Camp, Diadem, Care, Financial Aid\n"
        "   or SGO sources, fictional seed data, or strict preflight are missing.\n"
        "5. If the local servers start, open http://localhost:4173/sandbox.\n"
        "   For fictional SGO use http://localhost:4173/jireh-sgo/sign-in and the\n"
        "   locally generated private sgo-credentials.txt; never distribute it.\n"
        "\n"
        "Only fictional local test data. Do not enter real child/family information.\n"
        "Do not open loopback ports to the internet or activate external payments.\n"
        "An approved exact-SHA Windows and browser evidence bundle, and an owner\n"
        "laptop rehearsal, are required before any release certification.\n"
        "\n"
    ).encode("utf-8")


def build(
    output_directory: Path | None = None, *, source_sha: str | None = None,
    five_module_candidate: bool = False,
) -> Path:
    if five_module_candidate and source_sha is None:
        raise RuntimeError("Five-module candidate packaging requires an explicit source SHA")
    if source_sha is not None and not five_module_candidate:
        raise RuntimeError("Source SHA overrides require an explicit five-module candidate")
    sha = source_sha if source_sha is not None else pinned_revision()
    installer_bytes = render_installer(sha, five_module_candidate=five_module_candidate)
    readme_bytes = render_readme(sha, five_module_candidate=five_module_candidate)
    if five_module_candidate:
        require_exact_candidate_checkout(sha)
    output_directory = output_directory or ROOT / ".local-backups" / "heritage-sales"
    output_directory.mkdir(parents=True, exist_ok=True)
    target = output_directory / archive_name(sha, five_module_candidate=five_module_candidate)
    manifest = {
        "product": "CROWN Heritage Christian Academy local sales demo",
        "repository": "Arete0920/Crown-CSMS",
        "source_sha": sha,
        "source_url": f"https://github.com/Arete0920/Crown-CSMS/archive/{sha}.zip",
        "launch": "Start-Heritage.cmd",
        "entry": "http://localhost:4173/sandbox",
        "type": "isolated fictional-data local demo",
        "external_payments": False,
        "production_certified": False,
        "release_certified": False,
        "five_module_candidate": five_module_candidate,
    }
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name in STARTER_FILES:
            source = ROOT / name
            if not source.is_file():
                raise FileNotFoundError(f"Missing sales starter file: {name}")
            info = zipfile.ZipInfo(name, date_time=(2026, 10, 15, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            payload = (
                installer_bytes if name == "Install-and-Start-Heritage.py" else
                readme_bytes if name == "HERITAGE-LOCAL-DEMO-README.txt" else
                source.read_bytes()
            )
            archive.writestr(info, payload, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
        info = zipfile.ZipInfo("HERITAGE-SALES-MANIFEST.json", date_time=(2026, 10, 15, 0, 0, 0))
        info.compress_type = zipfile.ZIP_DEFLATED
        info.external_attr = 0o100644 << 16
        archive.writestr(info, json.dumps(manifest, indent=2) + "\n")
    with zipfile.ZipFile(target) as archive:
        if archive.testzip() is not None:
            raise RuntimeError("Sales package ZIP failed CRC verification")
    print(f"Heritage sales starter: {target}")
    print(f"Pinned CROWN source: {sha}")
    return target


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-sha", help="Exact Git checkout for a source-stamped candidate")
    parser.add_argument("--five-module-candidate", action="store_true",
                        help="Opt-in guarded launcher in an explicitly UNCERTIFIED candidate")
    args = parser.parse_args()
    build(source_sha=args.source_sha, five_module_candidate=args.five_module_candidate)
