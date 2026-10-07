#!/usr/bin/env python3
import json
import os
import re
import subprocess
from pathlib import Path

MANIFESTS = [
    ("backend/requirements.txt", "python"),
    ("frontend/dashboards/package.json", "node"),
    ("services/wallet/apple-pass-service/package.json", "node"),
]
REGISTER = Path("docs/security/dependency-admissions.json")

def git_show(base, path):
    result = subprocess.run(["git", "show", f"{base}:{path}"], text=True, capture_output=True)
    return result.stdout if result.returncode == 0 else ""

def python_deps(text):
    deps = set()
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or line.startswith("-"):
            continue
        name = re.split(r"[<>=!~\[; ]", line, maxsplit=1)[0].strip()
        if name:
            deps.add(name.lower().replace("_", "-"))
    return deps

def node_deps(text):
    if not text.strip():
        return set()
    data = json.loads(text)
    return set(data.get("dependencies", {})) | set(data.get("devDependencies", {}))

def parse(kind, text):
    return python_deps(text) if kind == "python" else node_deps(text)

def main():
    base = os.environ.get("CROWN_BASE_SHA", "").strip()
    if not re.fullmatch(r"[0-9a-f]{40}", base):
        raise SystemExit("CROWN_BASE_SHA must be a full commit SHA")
    register = json.loads(REGISTER.read_text(encoding="utf-8"))
    approved = {str(x.get("name", "")).lower() for x in register.get("admissions", [])}
    newly_added = set()
    for path, kind in MANIFESTS:
        current = Path(path).read_text(encoding="utf-8") if Path(path).exists() else ""
        prior = git_show(base, path)
        newly_added |= {x.lower() for x in parse(kind, current) - parse(kind, prior)}
    missing = sorted(x for x in newly_added if x not in approved)
    if missing:
        print("FAIL: new direct dependencies lack provenance admission records:")
        for name in missing:
            print(f"- {name}")
        print("Add reviewed entries to docs/security/dependency-admissions.json.")
        raise SystemExit(1)
    print("PASS: all newly introduced direct dependencies have admission records.")

if __name__ == "__main__":
    main()
