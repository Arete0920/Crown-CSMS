#!/usr/bin/env python3
"""Cross-layer integrity audit for the canonical CROWN dashboard module inventory.

This is a structural verification gate. It proves that the 40 canonical dashboard
modules remain aligned across frontend registration, data configuration, backend
payload contracts, certification metadata, and the ready-state shell/backend
contract. It intentionally does not promote draft modules or claim live-runtime
certification.
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

REGISTRY_PATH = ROOT / "frontend/dashboards/src/config/dashboardRegistry.js"
PATHS_PATH = ROOT / "frontend/dashboards/src/routes/paths.js"
DATA_REGISTRY_PATH = ROOT / "frontend/dashboards/src/config/dashboardDataRegistry.js"
CERT_REGISTRY_PATH = ROOT / "frontend/dashboards/src/config/dashboardCertificationRegistry.js"
SAMPLE_PAYLOADS_PATH = ROOT / "backend/crown_api/dashboards/sample_payloads.py"
EXTRA_PAYLOADS_PATH = ROOT / "backend/crown_api/dashboards/batch5_extra_payloads.py"
COMPLETENESS_PATH = ROOT / "frontend/dashboards/scripts/verify-dashboard-completeness.mjs"
SHELL_CONTRACT_PATH = ROOT / "contracts/shell_backend_contract.json"
CROWN_LAYOUT_PATH = ROOT / "frontend/dashboards/src/components/crown/CrownLayout.jsx"
ROUTER_PATH = ROOT / "frontend/dashboards/src/routes/router.jsx"

CANONICAL_MODULES = [
    ("attendance", "Attendance"),
    ("billing", "Billing"),
    ("financial-aid", "Financial Aid"),
    ("registrar", "Registrar"),
    ("scheduling", "Scheduling"),
    ("gradebook", "Gradebook"),
    ("student-care", "Student Care"),
    ("activities-athletics", "Activities & Athletics"),
    ("communications", "Communications"),
    ("school-administrator", "School Administrator"),
    ("school-board", "School Board"),
    ("master-control", "Master Control"),
    ("admissions", "Admissions"),
    ("advancement", "Advancement"),
    ("hr", "HR"),
    ("facilities", "Facilities"),
    ("health-office", "Health Office"),
    ("transportation", "Transportation"),
    ("food-service", "Food Service"),
    ("it-support", "IT Support"),
    ("fine-arts", "Fine Arts"),
    ("athletics-director", "Athletics Director"),
    ("library-media", "Library / Media"),
    ("extended-care", "Extended Care"),
    ("summer-camp", "Summer Camp"),
    ("safety-security", "Safety / Security"),
    ("curriculum-pd", "Curriculum / PD Hub"),
    ("chaplain-spiritual-life", "Chaplain / Spiritual Life"),
    ("advancement-operations", "Advancement Operations"),
    ("volunteer-management", "Volunteer Management"),
    ("portrait-service", "Portrait / Service Hours"),
    ("alumni-relations", "Alumni Relations"),
    ("network-benchmarking", "Network Benchmarking"),
    ("implementation-success", "Implementation Success"),
    ("data-migration", "Data Migration"),
    ("integrations-automation", "Integrations / Automation"),
    ("compliance-audit", "Compliance / Audit"),
    ("revenue-operations", "Revenue Operations"),
    ("release-reliability", "Release Reliability"),
    ("dashboard-certification-center", "Dashboard Certification Center"),
]

EXPECTED_KEYS = [key for key, _ in CANONICAL_MODULES]
EXPECTED_LABELS = [label for _, label in CANONICAL_MODULES]
EXPECTED_BY_KEY = dict(CANONICAL_MODULES)
READY_STATES = {"ready", "live", "production"}

failures: list[str] = []
warnings: list[str] = []
passes: list[str] = []


def read(path: Path) -> str:
    if not path.exists():
        failures.append(f"missing required file: {path.relative_to(ROOT)}")
        return ""
    return path.read_text(encoding="utf-8-sig")


def fail(message: str) -> None:
    failures.append(message)


def warn(message: str) -> None:
    warnings.append(message)


def passed(message: str) -> None:
    passes.append(message)


def compare_exact(name: str, actual: list[str], expected: list[str]) -> None:
    if actual == expected:
        passed(f"{name}: exact canonical set/order ({len(expected)})")
        return
    actual_set = set(actual)
    expected_set = set(expected)
    missing = [item for item in expected if item not in actual_set]
    extra = [item for item in actual if item not in expected_set]
    duplicates = sorted(item for item, count in Counter(actual).items() if count > 1)
    fail(
        f"{name}: mismatch; actual={len(actual)} expected={len(expected)} "
        f"missing={missing} extra={extra} duplicates={duplicates}"
    )


def compare_coverage(name: str, actual: set[str], expected: set[str]) -> None:
    missing = sorted(expected - actual)
    if missing:
        fail(f"{name}: missing canonical keys {missing}")
    else:
        passed(f"{name}: covers all {len(expected)} canonical dashboard keys")


def parse_paths(source: str) -> dict[str, str]:
    return {
        name: path
        for name, path in re.findall(
            r"^\s{2}([A-Z0-9_]+):\s*['\"]([^'\"]+)['\"]",
            source,
            flags=re.MULTILINE,
        )
    }


def parse_registry(source: str, paths: dict[str, str]) -> list[dict[str, str]]:
    marker = "export const DASHBOARD_REGISTRY = ["
    if marker not in source:
        fail("dashboard registry marker not found")
        return []
    body = source.split(marker, 1)[1].split("\n];", 1)[0]
    blocks = re.findall(
        r"createDashboard\(\{(.*?)(?=^\s{2}\}\),)",
        body,
        flags=re.DOTALL | re.MULTILINE,
    )
    entries: list[dict[str, str]] = []
    for block in blocks:
        key_match = re.search(r"^\s*key:\s*['\"]([^'\"]+)['\"]", block, flags=re.MULTILINE)
        label_match = re.search(r"^\s*label:\s*['\"]([^'\"]+)['\"]", block, flags=re.MULTILINE)
        path_token_match = re.search(r"^\s*path:\s*PATHS\.([A-Z0-9_]+)", block, flags=re.MULTILINE)
        path_literal_match = re.search(r"^\s*path:\s*['\"]([^'\"]+)['\"]", block, flags=re.MULTILINE)
        release_match = re.search(r"^\s*releaseState:\s*['\"]([^'\"]+)['\"]", block, flags=re.MULTILINE)
        module_key_match = re.search(r"^\s*moduleKey:\s*['\"]([^'\"]+)['\"]", block, flags=re.MULTILINE)

        if not key_match or not label_match:
            fail("unable to parse dashboard registry entry key/label")
            continue

        if path_token_match:
            path_value = paths.get(path_token_match.group(1), "")
            if not path_value:
                fail(f"registry key {key_match.group(1)} references unresolved PATHS.{path_token_match.group(1)}")
        elif path_literal_match:
            path_value = path_literal_match.group(1)
        else:
            path_value = ""
            fail(f"registry key {key_match.group(1)} has no parseable path")

        entries.append(
            {
                "key": key_match.group(1),
                "label": label_match.group(1),
                "path": path_value,
                "releaseState": release_match.group(1) if release_match else "draft",
                "moduleKey": module_key_match.group(1) if module_key_match else key_match.group(1),
            }
        )
    return entries


def parse_top_level_create_keys(source: str, marker: str, function_name: str) -> set[str]:
    if marker not in source:
        fail(f"missing source marker: {marker}")
        return set()
    body = source.split(marker, 1)[1].rsplit("};", 1)[0]
    keys: set[str] = set()
    pattern = re.compile(
        rf"^\s{{2}}(?:'([^']+)'|\"([^\"]+)\"|([A-Za-z][A-Za-z0-9_-]*)):\s*{re.escape(function_name)}",
        flags=re.MULTILINE,
    )
    for match in pattern.finditer(body):
        keys.add(next(group for group in match.groups() if group is not None))
    return keys


def parse_certification_keys(source: str) -> set[str]:
    marker = "export const DASHBOARD_CERTIFICATION_REGISTRY = {"
    if marker not in source:
        fail("dashboard certification registry marker not found")
        return set()
    body = source.split(marker, 1)[1].split("\n};", 1)[0]
    keys: set[str] = set()
    for match in re.finditer(
        r"^\s{2}(?:'([^']+)'|\"([^\"]+)\"|([A-Za-z][A-Za-z0-9_-]*)):\s*createCertification\(",
        body,
        flags=re.MULTILINE,
    ):
        keys.add(next(group for group in match.groups() if group is not None))
    return keys


def parse_python_mapping_keys(source: str, marker: str) -> set[str]:
    match = re.search(
        rf"^{re.escape(marker)}\s*=\s*\{{(.*?)^\}}",
        source,
        flags=re.DOTALL | re.MULTILINE,
    )
    if not match:
        fail(f"backend mapping not found: {marker}")
        return set()
    keys: set[str] = set()
    for key_match in re.finditer(
        r"^\s{4}(?:'([^']+)'|\"([^\"]+)\"|([A-Za-z][A-Za-z0-9_-]*)):\s*",
        match.group(1),
        flags=re.MULTILINE,
    ):
        keys.add(next(group for group in key_match.groups() if group is not None))
    return keys


registry_source = read(REGISTRY_PATH)
paths_source = read(PATHS_PATH)
data_source = read(DATA_REGISTRY_PATH)
cert_source = read(CERT_REGISTRY_PATH)
sample_source = read(SAMPLE_PAYLOADS_PATH)
extra_source = read(EXTRA_PAYLOADS_PATH)
completeness_source = read(COMPLETENESS_PATH)
layout_source = read(CROWN_LAYOUT_PATH)
router_source = read(ROUTER_PATH)

paths = parse_paths(paths_source)
registry_entries = parse_registry(registry_source, paths)
registry_keys = [entry["key"] for entry in registry_entries]
registry_labels = [entry["label"] for entry in registry_entries]
compare_exact("dashboard registry keys", registry_keys, EXPECTED_KEYS)
compare_exact("dashboard registry labels", registry_labels, EXPECTED_LABELS)

for entry in registry_entries:
    expected_label = EXPECTED_BY_KEY.get(entry["key"])
    if expected_label and entry["label"] != expected_label:
        fail(f"registry label mismatch for {entry['key']}: {entry['label']} != {expected_label}")

# Data registry can legitimately contain persona-only dashboards in addition to the 40.
data_keys = parse_top_level_create_keys(data_source, "export const DASHBOARD_DATA_REGISTRY = {", "create")
# The helper above matches createDataConfig/createDemoCriticalDataConfig by common prefix only when using a regex;
# perform the direct top-level key extraction to avoid depending on helper names.
data_body = data_source.split("export const DASHBOARD_DATA_REGISTRY = {", 1)[1].rsplit("};", 1)[0] if "export const DASHBOARD_DATA_REGISTRY = {" in data_source else ""
data_keys = set()
for match in re.finditer(
    r"^\s{2}(?:'([^']+)'|\"([^\"]+)\"|([A-Za-z][A-Za-z0-9_-]*)):\s*create(?:DemoCritical)?DataConfig\(",
    data_body,
    flags=re.MULTILINE,
):
    data_keys.add(next(group for group in match.groups() if group is not None))
compare_coverage("dashboard data registry", data_keys, set(EXPECTED_KEYS))

cert_keys = parse_certification_keys(cert_source)
compare_coverage("dashboard certification registry", cert_keys, set(EXPECTED_KEYS))

backend_keys = parse_python_mapping_keys(sample_source, "SAMPLE_PAYLOAD_BUILDERS")
backend_keys |= parse_python_mapping_keys(extra_source, "BATCH5_EXTRA_PAYLOAD_BUILDERS")
compare_exact("backend dashboard payload builders", sorted(backend_keys), sorted(EXPECTED_KEYS))

labels_match = re.search(
    r"const requiredDashboardLabels = \[(.*?)\];",
    completeness_source,
    flags=re.DOTALL,
)
if not labels_match:
    fail("dashboard completeness canonical label array not found")
else:
    completeness_labels = re.findall(r"['\"]([^'\"]+)['\"]", labels_match.group(1))
    compare_exact("dashboard completeness labels", completeness_labels, EXPECTED_LABELS)

ready_entries = [entry for entry in registry_entries if entry["releaseState"].lower() in READY_STATES]
draft_entries = [entry for entry in registry_entries if entry["releaseState"].lower() not in READY_STATES]
passed(f"release-state inventory parsed: ready={len(ready_entries)} non-ready={len(draft_entries)}")
if draft_entries:
    warn(
        "module completion remains unverified for non-ready registry entries: "
        + ", ".join(entry["key"] for entry in draft_entries)
    )

try:
    shell_contract = json.loads(read(SHELL_CONTRACT_PATH) or "{}")
except json.JSONDecodeError as exc:
    shell_contract = {}
    fail(f"shell backend contract is invalid JSON: {exc}")

expected_dashboard_contract = sorted(
    [
        {
            "moduleKey": entry["moduleKey"],
            "path": entry["path"],
            "apiContractKey": entry["key"],
        }
        for entry in ready_entries
    ],
    key=lambda row: row["path"],
)
actual_dashboard_contract = sorted(
    shell_contract.get("dashboardModules", []) if isinstance(shell_contract.get("dashboardModules", []), list) else [],
    key=lambda row: str(row.get("path", "")),
)
if actual_dashboard_contract != expected_dashboard_contract:
    fail(
        "ready dashboard shell/backend contract mismatch: "
        f"expected={expected_dashboard_contract} actual={actual_dashboard_contract}"
    )
else:
    passed(f"ready dashboard shell/backend contract aligned: {len(expected_dashboard_contract)} entries")

if "CONTRACT_NAV_ITEMS" in layout_source or "FALLBACK_NAV" in layout_source:
    fail("CrownLayout contains broad static navigation that can override or replace role-scoped navigation")
elif "EMPTY_ROLE_SCOPED_NAV" in layout_source and "Role-scoped navigation is hidden" in layout_source:
    passed("CrownLayout navigation failure mode is fail-closed")
else:
    warn("CrownLayout fail-closed navigation pattern could not be positively identified")

# Direct URL route guards remain a separate access-control concern. Backend APIs are the authority,
# but surface-level guards improve alignment and prevent unauthorized users from entering dead-end pages.
if re.search(r"path:\s*PATHS\.AFTERCARE_ROSTER,\s*element:\s*<AftercareRosterPage\s*/>", router_source, flags=re.DOTALL):
    warn("/aftercare/roster remains frontend-unguarded; backend aftercare APIs enforce role permissions")
if re.search(r"path:\s*PATHS\.COMMUNICATIONS_DIRECTOR,\s*element:\s*<CommunicationsDirectorDashboard\s*/>", router_source, flags=re.DOTALL):
    warn("/communications-director remains frontend-unguarded; direct-route role/permission alignment needs proof")

print("CROWN DASHBOARD MODULE INTEGRITY AUDIT")
print(f"canonical_modules={len(EXPECTED_KEYS)}")
print(f"ready_modules={len(ready_entries)}")
print(f"non_ready_modules={len(draft_entries)}")
print(f"passes={len(passes)} warnings={len(warnings)} failures={len(failures)}")

for message in passes:
    print(f"PASS: {message}")
for message in warnings:
    print(f"WARN: {message}")
for message in failures:
    print(f"FAIL: {message}")

if failures:
    sys.exit(1)
