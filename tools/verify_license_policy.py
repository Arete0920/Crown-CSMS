#!/usr/bin/env python3
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "docs/security/license-policy.json"

def load_records(path: Path):
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        for item in data:
            name = str(item.get("Name") or item.get("name") or "")
            version = str(item.get("Version") or item.get("version") or "")
            license_name = str(item.get("License") or item.get("license") or "")
            yield f"{name}=={version}".strip("="), license_name
        return
    if isinstance(data, dict):
        for package, metadata in data.items():
            if isinstance(metadata, dict):
                yield package, str(metadata.get("licenses") or metadata.get("license") or "")
        return
    raise SystemExit(f"Unsupported license report structure: {path}")

def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: verify_license_policy.py <license-report.json>")
    report = Path(sys.argv[1])
    policy = json.loads(POLICY.read_text(encoding="utf-8"))
    blocked = [x.upper() for x in policy["blocked_markers"]]
    review = [x.upper() for x in policy["review_required_markers"]]
    exceptions = {
        (x.get("package") if isinstance(x, dict) else x).lower()
        for x in policy.get("approved_review_exceptions", [])
        if (x.get("package") if isinstance(x, dict) else x)
    }
    ignored_projects = {
        str(x).lower() for x in policy.get("ignored_project_packages", [])
    }
    failures = []
    for package, license_name in load_records(report):
        if package.lower() in ignored_projects:
            continue
        normalized = license_name.strip().upper()
        if not normalized:
            failures.append(f"{package}: missing license")
            continue
        if any(marker in normalized for marker in blocked):
            failures.append(f"{package}: blocked license '{license_name}'")
            continue
        if any(marker in normalized for marker in review) and package.lower() not in exceptions:
            failures.append(f"{package}: license '{license_name}' requires explicit approval")
    if failures:
        print("FAIL: dependency license policy violations detected")
        for failure in failures:
            print(f"- {failure}")
        raise SystemExit(1)
    print(f"PASS: license policy satisfied for {report}")

if __name__ == "__main__":
    main()
