"""Build an auditable, minimal Windows starter for the approved Heritage local demo.

The ZIP intentionally excludes application source, secrets, databases and dependencies.
The first launch downloads an immutable commit from the authoritative public repository.
"""
from __future__ import annotations

import ast
import json
from pathlib import Path
import re
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


def build(output_directory: Path | None = None) -> Path:
    sha = pinned_revision()
    output_directory = output_directory or ROOT / ".local-backups" / "heritage-sales"
    output_directory.mkdir(parents=True, exist_ok=True)
    target = output_directory / f"CROWN-Heritage-Sales-Demo-{sha[:12]}.zip"
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
    }
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name in STARTER_FILES:
            source = ROOT / name
            if not source.is_file():
                raise FileNotFoundError(f"Missing sales starter file: {name}")
            info = zipfile.ZipInfo(name, date_time=(2026, 10, 15, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, source.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
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
    build()
