from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC_ROOT = ROOT / "tests" / "e2e"
OUT_DIR = ROOT / "audit-artifacts" / "wizard-e2e-evidence" / "latest"
SCOPE_FILE = ROOT / "scripts" / "execution" / "wizard_e2e_scope.json"

TRIVIAL_PATTERNS = [
    re.compile(r"expect\(\s*true\s*\)\.toBeTruthy\(\s*\)", re.I),
    re.compile(r"expect\(\s*1\s*\)\.toBe\(\s*1\s*\)", re.I),
    re.compile(r"expect\(\s*['\"]?ok['\"]?\s*\)\.toBeTruthy\(\s*\)", re.I),
]


def has_any(text: str, needles: tuple[str, ...]) -> bool:
    lower = text.lower()
    return any(needle.lower() in lower for needle in needles)


def classify_text(text: str, relative_path: str) -> dict:
    compact = re.sub(r"\s+", " ", text).strip()
    uses_page = has_any(text, ("page.goto(", "page.getby", "page.locator(", "page.click(", "page.fill("))
    uses_request = has_any(text, ("request.get(", "request.post(", "request.patch(", "request.put(", "request.delete("))
    uses_api_response = has_any(text, ("waitforresponse(", "response.status(", "/api/"))
    route_mocking = has_any(text, ("page.route(", "route.fulfill(", "route.continue("))
    persistence_signal = has_any(text, ("commit", "save", "submit", "persist", "reread", "verify", "created", "updated", "delete", "post(", "patch(", "put("))
    rbac_tenant_signal = has_any(text, ("unauthorized", "forbidden", "403", "401", "tenant", "school-id", "x-school-id", "cross-school", "foreign school", "wrong school", "denied"))
    validation_signal = has_any(text, ("validation", "invalid", "required", "error", "400"))
    constant_assertion = any(pattern.search(text) for pattern in TRIVIAL_PATTERNS)
    tiny = len(compact) < 220
    no_app_interaction = not (uses_page or uses_request or uses_api_response)

    if constant_assertion and tiny and no_app_interaction:
        classification = "PLACEHOLDER"
    elif uses_page and not persistence_signal:
        classification = "ROUTE_ONLY"
    elif uses_page or uses_request or uses_api_response:
        classification = "REAL_FUNCTIONAL_CANDIDATE"
    else:
        classification = "NON_EVIDENTIARY"

    scaffold_ui = uses_page
    live_ui_api = bool((uses_page or uses_request or uses_api_response) and not route_mocking)
    backend_persistence = bool(live_ui_api and persistence_signal)
    rbac_tenant = bool(live_ui_api and rbac_tenant_signal)
    proof_backed = bool(classification == "REAL_FUNCTIONAL_CANDIDATE" and live_ui_api and backend_persistence and rbac_tenant)

    return {
        "path": relative_path,
        "classification": classification,
        "SCAFFOLD_UI": scaffold_ui,
        "LIVE_UI_API": live_ui_api,
        "BACKEND_PERSISTENCE": backend_persistence,
        "RBAC_TENANT": rbac_tenant,
        "VALIDATION": validation_signal,
        "route_mocking": route_mocking,
        "constant_assertion": constant_assertion,
        "proof_backed": proof_backed,
    }


def load_scope() -> dict:
    if not SCOPE_FILE.exists():
        raise SystemExit(f"missing canonical wizard E2E scope file: {SCOPE_FILE}")
    scope = json.loads(SCOPE_FILE.read_text(encoding="utf-8"))
    canonical = scope.get("canonical_required", {})
    if len(canonical) != 28:
        raise SystemExit(f"canonical wizard scope must contain 28 registered wizards; found {len(canonical)}")
    return scope


def classify_path(relative_path: str) -> dict:
    path = ROOT / relative_path
    if not path.exists():
        return {
            "path": relative_path,
            "classification": "MISSING",
            "SCAFFOLD_UI": False,
            "LIVE_UI_API": False,
            "BACKEND_PERSISTENCE": False,
            "RBAC_TENANT": False,
            "VALIDATION": False,
            "route_mocking": False,
            "constant_assertion": False,
            "proof_backed": False,
        }
    return classify_text(path.read_text(encoding="utf-8", errors="replace"), relative_path)


def baseline_placeholder_count(ref: str, canonical_paths: list[str]) -> int:
    count = 0
    for relative in canonical_paths:
        if not relative:
            continue
        try:
            text = subprocess.check_output(["git", "show", f"{ref}:{relative}"], cwd=ROOT, text=True, stderr=subprocess.DEVNULL)
        except subprocess.CalledProcessError:
            continue
        if classify_text(text, relative)["classification"] == "PLACEHOLDER":
            count += 1
    return count


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fail-on-placeholder", action="store_true")
    parser.add_argument("--fail-on-unverified", action="store_true")
    parser.add_argument("--baseline-ref", default="", help="fail only if canonical placeholder debt increases relative to this git ref")
    args = parser.parse_args()

    scope = load_scope()
    canonical = scope["canonical_required"]
    duplicate_aliases = scope.get("duplicate_aliases", {})
    nonregistered_scope = scope.get("nonregistered_scope", [])
    retire = scope.get("retire", [])

    rows = []
    for slug, relative in canonical.items():
        row = classify_path(relative) if relative else {
            "path": None,
            "classification": "MISSING",
            "SCAFFOLD_UI": False,
            "LIVE_UI_API": False,
            "BACKEND_PERSISTENCE": False,
            "RBAC_TENANT": False,
            "VALIDATION": False,
            "route_mocking": False,
            "constant_assertion": False,
            "proof_backed": False,
        }
        rows.append({"slug": slug, **row})

    counts: dict[str, int] = {}
    for row in rows:
        counts[row["classification"]] = counts.get(row["classification"], 0) + 1

    placeholders = [row for row in rows if row["classification"] == "PLACEHOLDER"]
    missing = [row for row in rows if row["classification"] == "MISSING"]
    unverified = [row for row in rows if not row["proof_backed"]]
    canonical_paths = [path for path in canonical.values() if path]
    baseline_count = baseline_placeholder_count(args.baseline_ref, canonical_paths) if args.baseline_ref else None

    status = {
        "schema_version": 2,
        "canonical_registered_count": len(rows),
        "canonical_spec_file_count": len(canonical_paths),
        "duplicate_alias_count": len(duplicate_aliases),
        "nonregistered_scope_count": len(nonregistered_scope),
        "retire_count": len(retire),
        "classification_counts": counts,
        "placeholder_count": len(placeholders),
        "missing_count": len(missing),
        "baseline_placeholder_count": baseline_count,
        "placeholder_delta": None if baseline_count is None else len(placeholders) - baseline_count,
        "proof_backed_count": len(rows) - len(unverified),
        "unverified_count": len(unverified),
        "all_canonical_wizards_proof_backed": len(rows) == 28 and not unverified,
        "evidence_classes": ["SCAFFOLD_UI", "LIVE_UI_API", "BACKEND_PERSISTENCE", "RBAC_TENANT"],
        "duplicate_aliases": duplicate_aliases,
        "nonregistered_scope": nonregistered_scope,
        "retire": retire,
        "rows": rows,
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "99_STATUS.json").write_text(json.dumps(status, indent=2) + "\n", encoding="utf-8")
    summary = [
        "# Wizard E2E Evidence Classification", "",
        f"- Canonical registered wizards: {len(rows)}",
        f"- Canonical spec files mapped: {len(canonical_paths)}",
        f"- Missing canonical specs: {len(missing)}",
        f"- Duplicate alias specs excluded from denominator: {len(duplicate_aliases)}",
        f"- Nonregistered conceptual specs excluded from denominator: {len(nonregistered_scope)}",
        f"- Placeholder canonical specs: {len(placeholders)}",
        f"- Baseline canonical placeholders: {baseline_count if baseline_count is not None else 'n/a'}",
        f"- Proof-backed canonical wizards: {status['proof_backed_count']}/{len(rows)}", "",
        "| Wizard slug | Spec | Classification | Scaffold UI | Live UI/API | Persistence | RBAC/Tenant | Proof-backed |",
        "|---|---|---|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        summary.append(
            f"| `{row['slug']}` | `{row['path'] or 'MISSING'}` | {row['classification']} | "
            f"{str(row['SCAFFOLD_UI']).upper()} | {str(row['LIVE_UI_API']).upper()} | "
            f"{str(row['BACKEND_PERSISTENCE']).upper()} | {str(row['RBAC_TENANT']).upper()} | "
            f"{str(row['proof_backed']).upper()} |"
        )
    summary.extend(["", "## Excluded duplicate aliases"])
    summary.extend([f"- `{path}` -> `{slug}`" for path, slug in sorted(duplicate_aliases.items())] or ["- none"])
    summary.extend(["", "## Excluded nonregistered conceptual inventory"])
    summary.extend([f"- `{path}`" for path in nonregistered_scope] or ["- none"])
    (OUT_DIR / "00_SUMMARY.md").write_text("\n".join(summary) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in status.items() if k not in {"rows", "duplicate_aliases", "nonregistered_scope", "retire"}}, indent=2))

    if baseline_count is not None and len(placeholders) > baseline_count:
        print(f"ERROR: canonical placeholder debt regressed from {baseline_count} to {len(placeholders)}")
        return 4
    if args.fail_on_placeholder and placeholders:
        print("ERROR: placeholder canonical wizard specs remain:")
        for row in placeholders:
            print(f" - {row['slug']}: {row['path']}")
        return 2
    if args.fail_on_unverified and unverified:
        print("ERROR: canonical registered wizards remain without required live functional evidence")
        for row in unverified:
            print(f" - {row['slug']}: {row['classification']} ({row['path'] or 'missing spec'})")
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
